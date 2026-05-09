"""Environment-based application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    openai_api_key: str
    database_url: str
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 64

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from process environment variables."""
        return cls(
            openai_api_key=_required_env("OPENAI_API_KEY"),
            database_url=_required_env("SUPABASE_DB_URL"),
            embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            embedding_dimensions=int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536")),
            embedding_batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "64")),
        )


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
