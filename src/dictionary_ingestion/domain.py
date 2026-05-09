"""Core ingestion data models with no external runtime dependencies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageText:
    """Text extracted from one PDF page."""

    page: int
    text: str


@dataclass(frozen=True)
class DictionaryEntry:
    """A dictionary entry split from extracted page text."""

    source_title: str
    page: int
    language: str
    headword: str
    body: str


@dataclass(frozen=True)
class EmbeddedEntry:
    """A dictionary entry with its vector embedding."""

    entry: DictionaryEntry
    embedding: list[float]
