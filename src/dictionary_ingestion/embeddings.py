"""OpenAI embedding generation."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence

from openai import OpenAI

from dictionary_ingestion.domain import DictionaryEntry, EmbeddedEntry


class EmbeddingClient:
    """Small wrapper around the OpenAI embeddings API."""

    def __init__(self, *, api_key: str, model: str, dimensions: int | None = None) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    def embed_entries(
        self,
        entries: Sequence[DictionaryEntry],
        *,
        batch_size: int = 64,
    ) -> list[EmbeddedEntry]:
        """Generate embeddings for dictionary entries in batches."""
        embedded: list[EmbeddedEntry] = []
        for batch in _chunks(entries, batch_size):
            inputs = [entry_to_embedding_text(entry) for entry in batch]
            kwargs = {"model": self.model, "input": inputs}
            if self.dimensions:
                kwargs["dimensions"] = self.dimensions
            response = self.client.embeddings.create(**kwargs)
            embedded.extend(
                EmbeddedEntry(entry=entry, embedding=item.embedding)
                for entry, item in zip(batch, response.data, strict=True)
            )
        return embedded

    def embed_query(self, query: str) -> list[float]:
        """Generate a single query embedding."""
        kwargs = {"model": self.model, "input": query}
        if self.dimensions:
            kwargs["dimensions"] = self.dimensions
        response = self.client.embeddings.create(**kwargs)
        return response.data[0].embedding


def entry_to_embedding_text(entry: DictionaryEntry) -> str:
    """Format an entry for embedding with useful lexical context."""
    return (
        f"source_title: {entry.source_title}\n"
        f"language: {entry.language}\n"
        f"headword: {entry.headword}\n"
        f"definition: {entry.body}"
    )


def _chunks(items: Sequence[DictionaryEntry], size: int) -> Iterator[Sequence[DictionaryEntry]]:
    if size < 1:
        raise ValueError("batch size must be at least 1")
    for start in range(0, len(items), size):
        yield items[start : start + size]
