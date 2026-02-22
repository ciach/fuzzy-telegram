# AI-Powered Arras Contract System

Controlled legal document engine for **Arras Penitenciales (Catalonia)** with AI-assisted, validated mutations and full audit traceability.

## Purpose

This project is designed to prevent untracked legal text drift.  
Every mutation is structured, validated, and logged before it reaches a contract.

## Scope (Phase 1)

- Contract type: Arras Penitenciales (Catalonia)
- Languages: Spanish (canonical), Catalan, English
- Structured contract schema persisted in PostgreSQL (`JSONB`)
- AI assistant with domain-restricted actions only
- Manual clause editing with version history
- PDF and DOCX export
- Reference legal notes seeded from `pdf/CONTRATO ARRAS PENITENCIALES.docx (1).pdf`
- Deployment target: Fly.io

## Non-Negotiable Rules

1. Every mutation is logged in `contract_logs`.
2. AI never edits raw legal text directly.
3. AI can only return structured actions (for example `update_field`, `rewrite_clause`, `no_action`).
4. Derived financial values are server-side only (for example `remaining_amount`).
5. Manual clause edits are protected from accidental AI overwrite.

## Architecture

```text
Vue 3 (Vite)
  -> FastAPI API
    -> PostgreSQL (contracts, logs, clause versions)
    -> OpenAI API (structured assistant)
    -> Rendering engine (Jinja2 + PDF/DOCX)
```

## Python Stack (uv)

- Package manager / workflow: `uv`
- API: `fastapi`
- Validation: `pydantic`
- CLI/observability output: `rich`

### Bootstrap

```bash
uv sync --extra dev
```

### Environment setup

- Backend reads `.env` automatically (via `python-dotenv`).
- Example backend variables are in `.env.example`.
- Frontend example variables are in `frontend/.env.example`.

### Run API

```bash
uv run uvicorn backend.main:app --reload
```

### Run migrations (Alembic)

```bash
uv run alembic upgrade head
```

If you already have tables created outside Alembic and get `table ... already exists`:

```bash
# if local data is disposable
rm -f arras_dev.db
uv run alembic upgrade head

# if you must keep existing data/schema and trust it matches migration
uv run alembic stamp head
```

### Run tests

```bash
uv run pytest
```

### Export endpoints

- `POST /contracts/{id}/export/pdf` -> downloadable PDF
- `POST /contracts/{id}/export/docx` -> downloadable DOCX

### Voice agent intake endpoint

- `POST /contracts/{id}/voice-intake` with multipart field `audio_file`
- Pipeline:
  - transcription via OpenAI (`OPENAI_TRANSCRIPTION_MODEL`, default `whisper-1`)
  - structured multi-field extraction
  - validated updates applied to contract
- full AI interaction logging

## Fly.io Deployment

The repo includes:

- `fly.backend.toml` (FastAPI app)
- `fly.frontend.toml` (Vue static app via nginx)
- `backend/Dockerfile`
- `frontend/Dockerfile`

### 1. Create apps

```bash
fly apps create arras-contract-backend
fly apps create arras-contract-frontend
```

### 2. Provision Postgres and attach to backend

```bash
fly postgres create --name arras-contract-db --region mad
fly postgres attach --app arras-contract-backend arras-contract-db
```

`fly postgres attach` sets `DATABASE_URL` on backend.

### 3. Set backend secrets

```bash
fly secrets set -a arras-contract-backend OPENAI_API_KEY=your_key_here
fly secrets set -a arras-contract-backend OPENAI_MODEL=gpt-5-mini
fly secrets set -a arras-contract-backend OPENAI_TRANSCRIPTION_MODEL=whisper-1
fly secrets set -a arras-contract-backend CORS_ORIGINS=https://arras-contract-frontend.fly.dev
```

### 4. Deploy backend

```bash
fly deploy -c fly.backend.toml
```

### 5. Deploy frontend

If backend URL is different from `https://arras-contract-backend.fly.dev`, edit `VITE_API_BASE_URL`
in `fly.frontend.toml` first.

```bash
fly deploy -c fly.frontend.toml
```

### 6. Health checks

- Backend: `https://arras-contract-backend.fly.dev/healthz`
- Frontend: `https://arras-contract-frontend.fly.dev/healthz`

## Frontend (Vue 3 + Vite)

### Install and run

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### Production build check

```bash
cd frontend
npm run build
```

Frontend default API target is `http://127.0.0.1:8000` and can be overridden with `VITE_API_BASE_URL`.

## Current Backend Status (2026-02-14)

- Implemented FastAPI app entrypoint in `backend/main.py`
- Implemented Vue 3 + Vite frontend scaffold in `frontend/` with:
  - dashboard
  - contract editor split layout (form + live preview + chat + logs)
  - tabbed editor sections for metadata, parties, property, financial, legal clauses
  - example placeholders for legal/field inputs
  - legal clause editor shown only on the legal-clauses tab
  - history page
  - Pinia stores for contracts/chat
  - browser microphone voice-intake component
- Implemented endpoints:
  - `POST /contracts`
  - `GET /contracts/{id}`
  - `PATCH /contracts/{id}`
  - `POST /contracts/{id}/chat`
  - `GET /contracts/{id}/logs`
  - `GET /contracts/{id}/ai-interactions`
  - `POST /contracts/{id}/export/pdf`
  - `POST /contracts/{id}/export/docx`
  - `POST /contracts/{id}/voice-intake`
- Implemented strict mutation validation and derived financial recalculation
- Implemented audit log creation for every mutation
- Implemented atomic persistence for mutation + audit log (+ clause version when applicable)
- Implemented AI interaction logging for every chat attempt (applied and non-applied)
- Implemented manual-clause lock that blocks AI rewrite unless override is explicit
- Implemented SQLAlchemy persistence with PostgreSQL-ready schema and Alembic migration
- Implemented legal clause seeding from reference PDF (with safe fallback)
- Legal clauses support placeholders for automatic propagation:
  - `{{buyers_names}}`, `{{sellers_names}}`
  - `{{total_price_eur}}`, `{{arras_amount_eur}}`, `{{remaining_amount_eur}}`
  - `{{deadline_date}}`, `{{property_address}}`
- Implemented frontend export buttons (DOCX/PDF)
- Runtime clause extraction uses `pdftotext` when available; otherwise fallback clauses are applied
- Voice extraction can map transcript data to:
  - buyers/sellers (with IDs)
  - property fields
  - financial fields
  - metadata fields

## Database

- Runtime persistence uses SQLAlchemy store (`backend/storage/sqlalchemy_store.py`)
- Migrations are managed with Alembic (`alembic/`, `alembic.ini`)
- Default local DB URL: `sqlite:///./arras_dev.db` (override with `DATABASE_URL`)
- `AUTO_CREATE_SCHEMA` defaults to `false` to avoid migration drift/conflicts
- `CORS_ORIGINS` controls allowed frontend origins (default: `http://localhost:5173,http://127.0.0.1:5173`)
- `CORS_ORIGIN_REGEX` allows local-network dev origins by default (`localhost`, `127.0.0.1`, `192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`)
- `OPENAI_TRANSCRIPTION_MODEL` defaults to `whisper-1`
- Production target: PostgreSQL (Fly managed Postgres)

## Documentation Contract

The following files are required and must stay synchronized:

- `readme.md`: project overview, setup, architecture, runtime workflow
- `agents.md`: contributor and AI-agent operating rules
- `implementation.md`: phased implementation plan and acceptance criteria

If architecture, schema, security policy, mutation logic, or roadmap changes, update all impacted docs in the same change.
