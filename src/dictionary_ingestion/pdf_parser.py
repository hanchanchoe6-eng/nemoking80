"""PDF text extraction utilities."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader

from dictionary_ingestion.domain import PageText


def extract_pages(pdf_path: str | Path | BinaryIO) -> tuple[str, list[PageText]]:
    """Extract text from each PDF page.

    Returns the PDF title from metadata when present and a list of 1-indexed
    page text objects. Empty pages are represented with an empty string so that
    downstream page numbers remain aligned with the source PDF.
    """
    reader = PdfReader(pdf_path)
    metadata_title = ""
    if reader.metadata and reader.metadata.title:
        metadata_title = str(reader.metadata.title).strip()

    pages = [
        PageText(page=index + 1, text=(page.extract_text() or "").strip())
        for index, page in enumerate(reader.pages)
    ]
    return metadata_title, pages
