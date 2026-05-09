# PDF Dictionary Ingestion Pipeline

This project ingests uploaded PDF dictionaries, splits page text into lexical entries, embeds each entry with the OpenAI Embeddings API, stores the vectors in a Supabase PostgreSQL `pgvector` table, and exposes exact lemma and semantic vector search APIs.

## Features

1. Extracts text from each PDF page with page numbers preserved.
2. Detects dictionary headwords with a configurable regular expression and splits text into entries.
3. Attaches `source_title`, `page`, `language`, and `headword` metadata to every entry.
4. Generates OpenAI embeddings in batches.
5. Stores entries and vectors in Supabase PostgreSQL using `pgvector`.
6. Provides a FastAPI service for PDF upload ingestion, exact lemma search, and natural-language vector search.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements-dev.txt
copy .env.example .env
```

Set the values in `.env` or export them in your shell:

- `OPENAI_API_KEY`: OpenAI API key used for embeddings.
- `SUPABASE_DB_URL`: Supabase PostgreSQL connection string. Use the direct database URL or a pooler URL that supports prepared statements as configured for your project.
- `OPENAI_EMBEDDING_MODEL`: defaults to `text-embedding-3-small`.
- `OPENAI_EMBEDDING_DIMENSIONS`: defaults to `1536`; keep this aligned with the `embedding vector(1536)` column in `sql/schema.sql`.
- `EMBEDDING_BATCH_SIZE`: defaults to `64`.

## Database schema

Run the schema in the Supabase SQL editor or with `psql`:

```bash
psql "$SUPABASE_DB_URL" -f sql/schema.sql
```

If you change `OPENAI_EMBEDDING_DIMENSIONS`, update the `embedding vector(...)` size in `sql/schema.sql` before creating the table.

## Ingest a PDF from the CLI

```bash
PYTHONPATH=src python -m dictionary_ingestion.ingest ./my-dictionary.pdf --language en --source-title "My Dictionary"
```

On Windows PowerShell, prefix commands with `$env:PYTHONPATH = "src"` once per shell session:

```powershell
$env:PYTHONPATH = "src"
py -m dictionary_ingestion.ingest .\my-dictionary.pdf --language en --source-title "My Dictionary"
```

For dictionaries with a custom layout, pass a regex that contains a named `headword` group. The regex is matched against each normalized line:

```bash
PYTHONPATH=src python -m dictionary_ingestion.ingest ./latin.pdf \
  --language la \
  --headword-regex '^(?P<headword>[A-Z][A-Za-z-]+)\\s+\\[[^]]+\\]'
```

The default headword detector expects a line to begin with a headword followed by a colon, an en/em dash separator, a hyphen separator, or multiple spaces.

## Run the API

```bash
PYTHONPATH=src python -m uvicorn dictionary_ingestion.api:app --host 0.0.0.0 --port 8000
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
py -m uvicorn dictionary_ingestion.api:app --host 0.0.0.0 --port 8000
```

The service starts at `http://localhost:8000`.

### Upload and ingest a PDF

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@./my-dictionary.pdf" \
  -F "language=en" \
  -F "source_title=My Dictionary"
```

### Exact lemma search

```bash
curl 'http://localhost:8000/search/exact?lemma=water&language=en&limit=10'
```

### Natural-language vector search

```bash
curl -X POST http://localhost:8000/search/vector \
  -H 'content-type: application/json' \
  -d '{"query":"words related to rivers and rain","language":"en","limit":5}'
```

## Project layout

- `src/dictionary_ingestion/pdf_parser.py`: page-by-page PDF extraction.
- `src/dictionary_ingestion/splitter.py`: headword detection and entry splitting.
- `src/dictionary_ingestion/embeddings.py`: OpenAI embedding generation.
- `src/dictionary_ingestion/store.py`: Supabase PostgreSQL and `pgvector` persistence/search.
- `src/dictionary_ingestion/ingest.py`: CLI and reusable ingestion orchestration.
- `src/dictionary_ingestion/api.py`: FastAPI upload and search endpoints.
- `sql/schema.sql`: required Supabase table, extension, and indexes.
