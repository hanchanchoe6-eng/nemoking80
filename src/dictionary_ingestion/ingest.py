"""Command-line and programmatic ingestion pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from dictionary_ingestion.config import Settings
from dictionary_ingestion.embeddings import EmbeddingClient
from dictionary_ingestion.domain import DictionaryEntry, EmbeddedEntry
from dictionary_ingestion.pdf_parser import extract_pages
from dictionary_ingestion.splitter import compile_headword_pattern, split_entries
from dictionary_ingestion.store import PgVectorStore


def ingest_pdf(
    pdf_path: str | Path,
    *,
    source_title: str | None,
    language: str,
    headword_regex: str | None = None,
    settings: Settings | None = None,
) -> int:
    """Run the full PDF-to-pgvector ingestion pipeline."""
    runtime_settings = settings or Settings.from_env()
    metadata_title, pages = extract_pages(pdf_path)
    title = source_title or metadata_title or Path(pdf_path).stem
    pattern = compile_headword_pattern(headword_regex)
    entries = split_entries(pages, source_title=title, language=language, headword_pattern=pattern)
    return ingest_entries(entries, settings=runtime_settings)


def ingest_entries(entries: list[DictionaryEntry], *, settings: Settings | None = None) -> int:
    """Embed and store already-split dictionary entries."""
    runtime_settings = settings or Settings.from_env()
    embedding_client = EmbeddingClient(
        api_key=runtime_settings.openai_api_key,
        model=runtime_settings.embedding_model,
        dimensions=runtime_settings.embedding_dimensions,
    )
    embedded_entries: list[EmbeddedEntry] = embedding_client.embed_entries(
        entries,
        batch_size=runtime_settings.embedding_batch_size,
    )
    with PgVectorStore(runtime_settings.database_url) as store:
        return store.insert_entries(embedded_entries)


def build_parser() -> argparse.ArgumentParser:
    """Build the ingestion CLI argument parser."""
    parser = argparse.ArgumentParser(description="Ingest a PDF dictionary into Supabase pgvector.")
    parser.add_argument("pdf", type=Path, help="Path to the source PDF dictionary")
    parser.add_argument("--language", required=True, help="Language code or label for the dictionary entries")
    parser.add_argument("--source-title", help="Source title metadata; defaults to PDF title or filename")
    parser.add_argument(
        "--headword-regex",
        help="Custom regex with a named (?P<headword>...) group for entry starts",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    args = build_parser().parse_args()
    count = ingest_pdf(
        args.pdf,
        source_title=args.source_title,
        language=args.language,
        headword_regex=args.headword_regex,
    )
    print(f"Inserted {count} dictionary entries")


if __name__ == "__main__":
    main()
