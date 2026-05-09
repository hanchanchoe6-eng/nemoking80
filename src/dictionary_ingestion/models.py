"""Pydantic API models for dictionary ingestion and search."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EntryResponse(BaseModel):
    """API response object for a stored dictionary entry."""

    id: UUID
    source_title: str
    page: int
    language: str
    headword: str
    body: str
    score: float | None = None


class ExactSearchResponse(BaseModel):
    """Exact-search API response."""

    lemma: str
    results: list[EntryResponse]


class VectorSearchRequest(BaseModel):
    """Request body for semantic vector search."""

    query: str = Field(min_length=1)
    language: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class VectorSearchResponse(BaseModel):
    """Vector-search API response."""

    query: str
    results: list[EntryResponse]


class IngestResponse(BaseModel):
    """Ingestion API response."""

    source_title: str
    language: str
    entries_inserted: int


def row_to_entry_response(row: dict[str, Any]) -> EntryResponse:
    """Convert a database row dictionary to an API response model."""
    return EntryResponse(
        id=row["id"],
        source_title=row["source_title"],
        page=row["page"],
        language=row["language"],
        headword=row["headword"],
        body=row["body"],
        score=row.get("score"),
    )
