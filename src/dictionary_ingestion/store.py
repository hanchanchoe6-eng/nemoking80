"""Supabase PostgreSQL/pgvector persistence and search."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from dictionary_ingestion.domain import EmbeddedEntry


class PgVectorStore(AbstractContextManager["PgVectorStore"]):
    """Repository for dictionary entries stored in a pgvector table."""

    def __init__(self, database_url: str) -> None:
        self.conn = psycopg.connect(database_url, row_factory=dict_row)
        register_vector(self.conn)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        self.close()
        return None

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def insert_entries(self, embedded_entries: Iterable[EmbeddedEntry]) -> int:
        """Insert embedded entries and return the number of rows inserted."""
        rows = [
            (
                item.entry.source_title,
                item.entry.page,
                item.entry.language,
                item.entry.headword,
                item.entry.body,
                item.embedding,
            )
            for item in embedded_entries
        ]
        if not rows:
            return 0

        with self.conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO dictionary_entries
                    (source_title, page, language, headword, body, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                rows,
            )
        self.conn.commit()
        return len(rows)

    def exact_search(
        self,
        lemma: str,
        *,
        language: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return entries whose headword exactly matches a lemma, case-insensitively."""
        params: list[Any] = [lemma]
        language_clause = ""
        if language:
            language_clause = "AND language = %s"
            params.append(language)
        params.append(limit)

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, source_title, page, language, headword, body, NULL::double precision AS score
                FROM dictionary_entries
                WHERE lower(headword) = lower(%s)
                {language_clause}
                ORDER BY source_title, page, headword
                LIMIT %s
                """,
                params,
            )
            return list(cur.fetchall())

    def vector_search(
        self,
        embedding: list[float],
        *,
        language: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return nearest entries by cosine distance using pgvector."""
        language_clause = ""
        params: list[Any] = [embedding]
        if language:
            language_clause = "WHERE language = %s"
            params.append(language)
        params.extend([embedding, limit])

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    id,
                    source_title,
                    page,
                    language,
                    headword,
                    body,
                    1 - (embedding <=> %s) AS score
                FROM dictionary_entries
                {language_clause}
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                params,
            )
            return list(cur.fetchall())
