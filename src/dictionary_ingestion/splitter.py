"""Heuristics for splitting dictionary page text into entries."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Pattern

from dictionary_ingestion.domain import DictionaryEntry, PageText

DEFAULT_HEADWORD_PATTERN = r"^(?P<headword>[A-Za-zÀ-ÖØ-öø-ÿĀ-ſƀ-ɏḀ-ỿ가-힣][\w'’\-·. ]{0,80})(?:\s{2,}|\s+[–—-]\s+|\s*[:：])"


def compile_headword_pattern(pattern: str | None = None) -> Pattern[str]:
    """Compile a configurable headword detector.

    The regex must expose a named group called ``headword``. The default looks
    for a headword at the beginning of a line followed by a colon, dash, or
    multiple spaces, which covers many scanned/OCR dictionary layouts.
    """
    compiled = re.compile(pattern or DEFAULT_HEADWORD_PATTERN)
    if "headword" not in compiled.groupindex:
        raise ValueError("Headword regex must include a named group: (?P<headword>...)")
    return compiled


def split_entries(
    pages: Iterable[PageText],
    *,
    source_title: str,
    language: str,
    headword_pattern: Pattern[str] | None = None,
) -> list[DictionaryEntry]:
    """Split page text into dictionary entries and attach metadata."""
    pattern = headword_pattern or compile_headword_pattern()
    entries: list[DictionaryEntry] = []
    current_headword: str | None = None
    current_page: int | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_headword, current_page, current_lines
        if current_headword and current_page and current_lines:
            body = "\n".join(line.strip() for line in current_lines if line.strip()).strip()
            if body:
                entries.append(
                    DictionaryEntry(
                        source_title=source_title,
                        page=current_page,
                        language=language,
                        headword=current_headword,
                        body=body,
                    )
                )
        current_headword = None
        current_page = None
        current_lines = []

    for page in pages:
        for raw_line in page.text.splitlines():
            line = normalize_line(raw_line)
            if not line:
                continue

            match = pattern.match(line)
            if match:
                flush()
                current_headword = normalize_headword(match.group("headword"))
                current_page = page.page
                current_lines = [line]
            elif current_headword:
                current_lines.append(line)

    flush()
    return entries


def normalize_line(line: str) -> str:
    """Normalize whitespace and common OCR punctuation spacing."""
    return re.sub(r"\s+", " ", line.replace("\u00a0", " ")).strip()


def normalize_headword(headword: str) -> str:
    """Normalize a detected headword while preserving display casing."""
    return headword.strip(" \t:：–—-")
