CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS dictionary_entries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_title text NOT NULL,
    page integer NOT NULL CHECK (page > 0),
    language text NOT NULL,
    headword text NOT NULL,
    body text NOT NULL,
    embedding vector(1536) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS dictionary_entries_headword_idx
    ON dictionary_entries (lower(headword));

CREATE INDEX IF NOT EXISTS dictionary_entries_language_idx
    ON dictionary_entries (language);

CREATE INDEX IF NOT EXISTS dictionary_entries_embedding_cosine_idx
    ON dictionary_entries USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
