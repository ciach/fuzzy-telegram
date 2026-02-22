# Implementation Plan

Project: AI-Powered Arras Contract System  
Domain: Arras Penitenciales (Catalonia)  
Backend baseline: OpenAI + FastAPI + Pydantic + PostgreSQL  
Frontend baseline: Vue 3 + Vite

## 0. Current Status (2026-02-14)

Implemented in code:

- FastAPI backend scaffold with router split under `backend/api/routers/`
- Vue 3 + Vite frontend scaffold with pages/components/stores:
  - `Dashboard.vue`
  - `ContractEditor.vue`
  - `ContractHistory.vue`
  - `ContractFormTabs.vue`, `ClauseEditor.vue`, `LivePreview.vue`, `ChatAssistant.vue`, `ChangeLogPanel.vue`
- Form tabs now include editable metadata/parties/property/financial sections with example placeholders
- Legal clause editor is tab-gated to `legal clauses` view
- Contract create/read/update endpoints
- Export endpoints now generate real downloadable DOCX and PDF artifacts
- New contracts are pre-seeded with legal clauses parsed from reference PDF
- Clause text supports placeholders that auto-resolve in exports using current contract values
- Voice intake flow implemented: browser audio capture -> transcription -> structured updates -> validated apply/log
- `.env` autoload enabled with backend/frontend `.env.example` templates
- Fly.io deployment assets added (backend/frontend Dockerfiles + Fly configs + health checks)
- AI chat endpoint with structured action parsing and safe fallback (`no_action`)
- AI interaction log endpoint (`GET /contracts/{id}/ai-interactions`)
- Strict dot-path mutation validator
- Derived `financial.remaining_amount` enforcement on every mutation
- Full in-app mutation logging payload (`old_value`, `new_value`, actor, AI prompt/response)
- Atomic mutation persistence (contract update + log write + clause version write)
- Full AI prompt/response interaction logging (including no-action and rejected mutations)
- Manual clause lock that blocks AI override unless explicit flag is passed
- SQLAlchemy persistence layer and Alembic migration baseline
- Unit tests for core mutation and locking behavior
- Automatic schema creation is disabled by default; Alembic is the migration authority
- CORS middleware enabled for local frontend origins to support browser preflight requests

Still pending:

- Auth/RBAC and rate limiting

## 1. Scope Definition

### Phase 1 Objectives

- Single contract family: Arras Penitenciales
- Canonical data language: Spanish
- Additional outputs: Catalan and English
- Structured contract schema in DB
- Full audit trail for all mutations
- AI chat assistant with domain restrictions
- Manual clause editing support
- PDF and DOCX export
- Fly.io deployment

## 2. Architecture

```text
Frontend (Vue 3)
  -> Backend API (FastAPI)
    -> PostgreSQL (contracts, logs, clause versions)
    -> OpenAI API (structured legal assistant)
    -> Rendering service (Jinja2 + DOCX/PDF)
```

## 3. Backend Design (FastAPI)

### 3.1 Module Layout

```text
frontend/
  src/
    pages/
      Dashboard.vue
      ContractEditor.vue
      ContractHistory.vue
    components/
      ContractFormTabs.vue
      ClauseEditor.vue
      LivePreview.vue
      ChatAssistant.vue
      ChangeLogPanel.vue
    stores/
      contractStore.ts
      chatStore.ts

backend/
  core/
    config.py
  api/
    routers/
      contracts.py
      chat.py
      export.py
    presenters.py
  storage/
    in_memory_store.py
    sqlalchemy_store.py
    store_protocol.py
  db/
    base.py
    models.py
    session.py
  dependencies.py
  main.py
  services/
    contract_service.py
    ai_service.py
    rendering_service.py
    logging_service.py
  models/
    contract_model.py
    clause_model.py
    log_model.py
  schemas/
    contract_schema.py
    ai_actions.py
```

### 3.2 Core API Endpoints

- `POST /contracts` create draft contract
- `GET /contracts/{id}` fetch contract
- `PATCH /contracts/{id}` user mutation with logging
- `POST /contracts/{id}/chat` AI action proposal and application
- `POST /contracts/{id}/voice-intake` voice transcript extraction and bulk field updates
- `GET /contracts/{id}/logs` full audit history
- `GET /contracts/{id}/ai-interactions` full AI prompt/response history
- `POST /contracts/{id}/export/docx` export DOCX
- `POST /contracts/{id}/export/pdf` export PDF

## 4. Data Model (PostgreSQL)

### 4.1 `contracts`

- `id UUID PK`
- `language TEXT CHECK (...)`
- `status TEXT CHECK (draft, finalized)`
- `schema_json JSONB NOT NULL`
- `created_at TIMESTAMP`
- `updated_at TIMESTAMP`

### 4.2 `contract_logs` (critical)

- `id UUID PK`
- `contract_id UUID FK -> contracts(id)`
- `action_type TEXT`
- `field_path TEXT`
- `old_value JSONB`
- `new_value JSONB`
- `triggered_by TEXT CHECK (user, ai)`
- `ai_prompt TEXT`
- `ai_response TEXT`
- `created_at TIMESTAMP`

### 4.3 `clause_versions`

- `id UUID PK`
- `contract_id UUID FK`
- `clause_id TEXT`
- `version_no INT`
- `content TEXT`
- `triggered_by TEXT`
- `created_at TIMESTAMP`

Used in current implementation for persistent manual-clause edit detection and future rollback support.

### 4.4 `ai_interactions`

- `id UUID PK`
- `contract_id UUID FK`
- `prompt TEXT`
- `raw_response TEXT`
- `parsed_action JSONB`
- `status TEXT`
- `error TEXT`
- `created_at TIMESTAMP`

## 5. Contract Schema Rules

Canonical schema remains structured, not raw-text-first:

```json
{
  "metadata": {
    "location": "Olerdola",
    "date": "2025-06-01",
    "language": "es"
  },
  "parties": {
    "sellers": [],
    "buyers": []
  },
  "property": {
    "address": "",
    "registry": "",
    "cargas": [],
    "ibi": 0
  },
  "financial": {
    "total_price": 45500,
    "arras_amount": 4550,
    "remaining_amount": 40950,
    "deadline": "2025-08-29"
  },
  "clauses": {
    "clause_1": "...",
    "clause_2": "...",
    "clause_3": "..."
  }
}
```

Derived values are backend-computed only.

## 6. AI Mutation Layer

### 6.1 Output Contract

Only accept structured actions:

```json
{"action":"update_field","path":"financial.arras_amount","value":6000}
```

or

```json
{"action":"rewrite_clause","clause_id":"clause_2","new_text":"..."}
```

or

```json
{"action":"no_action","reason":"insufficient_data"}
```

### 6.2 Validation Pipeline

1. Parse JSON into Pydantic model
2. Validate action type and required fields
3. Verify path existence and value types
4. Run legal/business validators
5. Apply mutation transactionally (DB-backed service in current implementation)
6. Log mutation with prompt/response metadata

Reject on first validation failure.

## 7. Multilingual Strategy

Recommended: canonical Spanish schema plus translated clause variants.

- source of truth: Spanish
- generated variants: Catalan, English
- translation events logged
- export template chosen by target language

## 8. Document Generation

### 8.1 Templates

- `templates/contract_es.j2`
- `templates/contract_ca.j2`
- `templates/contract_en.j2`

### 8.2 DOCX

- `python-docx`
- token replacement against controlled placeholders

### 8.3 PDF

- preferred: HTML render + WeasyPrint
- fallback: DOCX conversion pipeline if required by formatting constraints

## 9. Security and Compliance

- authenticated access required
- role model: `agent`, `admin`
- per-user action traceability
- AI endpoint rate limiting
- secure secret management in Fly.io env vars
- encrypted DB backups

## 10. Deployment (Fly.io)

### 10.1 Runtime Topology

- frontend app container
- backend app container
- managed Postgres

### 10.2 Required Environment Variables

- `OPENAI_API_KEY`
- `DATABASE_URL`
- `APP_ENV`

## 11. Roadmap

### Phase 1 (4-6 weeks)

- schema and validators
- Vue editor baseline
- FastAPI endpoints
- structured AI assistant
- audit logging engine
- Spanish-only workflow

### Phase 2

- Catalan and English templates
- DOCX/PDF export hardening
- clause versioning and rollback UI

### Phase 3

- clause library and toggles
- risk warning engine
- analytics dashboard
- digital signature integration
- multi-document support

## 12. Acceptance Criteria

1. No contract mutation can bypass `contract_logs`.
2. Invalid AI output cannot mutate state.
3. Derived financial fields are always consistent.
4. Manual clause changes remain recoverable with version history.
5. Spanish, Catalan, and English exports produce semantically equivalent documents.

## 13. Documentation Maintenance Rule

Whenever implementation details change, update:

- `readme.md` for setup/usage changes
- `agents.md` for rule/policy changes
- `implementation.md` for architecture/roadmap changes

These updates are part of definition-of-done.
