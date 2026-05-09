"""FastAPI application for dictionary ingestion and search."""

from __future__ import annotations

import tempfile
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, Query, UploadFile

from dictionary_ingestion.config import Settings
from dictionary_ingestion.embeddings import EmbeddingClient
from dictionary_ingestion.ingest import ingest_pdf
from dictionary_ingestion.models import (
    ExactSearchResponse,
    IngestResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    row_to_entry_response,
)
from dictionary_ingestion.store import PgVectorStore

app = FastAPI(
    title="PDF Dictionary Ingestion API",
    summary="Ingest PDF dictionaries and search entries by lemma or semantic query.",
)


@app.post("/ingest", response_model=IngestResponse)
async def ingest_upload(
    file: UploadFile = File(...),
    language: str = Form(...),
    source_title: str | None = Form(default=None),
    headword_regex: str | None = Form(default=None),
) -> IngestResponse:
    """Upload a PDF dictionary and store embedded entries in pgvector."""
    title = source_title or Path(file.filename or "uploaded-dictionary").stem
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp.flush()
        count = ingest_pdf(
            tmp.name,
            source_title=title,
            language=language,
            headword_regex=headword_regex,
        )
    return IngestResponse(source_title=title, language=language, entries_inserted=count)


@app.get("/search/exact", response_model=ExactSearchResponse)
def exact_search(
    lemma: str = Query(..., min_length=1),
    language: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> ExactSearchResponse:
    """Find entries whose headword exactly matches ``lemma``."""
    settings = Settings.from_env()
    with PgVectorStore(settings.database_url) as store:
        rows = store.exact_search(lemma, language=language, limit=limit)
    return ExactSearchResponse(lemma=lemma, results=[row_to_entry_response(row) for row in rows])


@app.post("/search/vector", response_model=VectorSearchResponse)
def vector_search(request: VectorSearchRequest) -> VectorSearchResponse:
    """Embed a natural-language query and find semantically similar entries."""
    settings = Settings.from_env()
    embedding_client = EmbeddingClient(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )
    embedding = embedding_client.embed_query(request.query)
    with PgVectorStore(settings.database_url) as store:
        rows = store.vector_search(embedding, language=request.language, limit=request.limit)
    return VectorSearchResponse(query=request.query, results=[row_to_entry_response(row) for row in rows])


def main() -> None:
    """Run the API with Uvicorn."""
    uvicorn.run("dictionary_ingestion.api:app", host="0.0.0.0", port=8000, reload=False)
