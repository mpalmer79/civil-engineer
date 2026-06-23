# Civil Engineer AI Backend

FastAPI backend for Civil Engineer AI: Stormwater Review Assistant. This is the
Phase 4 backend. It serves seeded Brookside Meadows review data, document chunks,
and source evidence, and it runs a controlled AI review workflow that produces
draft review-support findings.

Civil Engineer AI is a review-support and evidence-organization system. It does
not approve plans, certify compliance, stamp drawings, or replace a licensed
Professional Engineer. Statuses, retrieval results, and AI draft findings never
use final-decision language, and every AI draft finding requires human review.

The AI Review Assistant uses a deterministic mock provider by default, so the
backend runs without any API key. Live provider calls are disabled by default.
Phase 4 does not include embeddings, a vector store, or authentication.

## Requirements

- Python 3.11 or newer

## Setup

From the `backend` directory:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # optional, defaults work without it
```

## Seed the database

The database is also seeded automatically on first startup if it is empty. To
seed (or reset and reseed) explicitly:

```bash
python -m app.db.seed
```

This loads the Brookside Meadows fixture: 19 documents, 19 checklist items, 10
findings, 10 audit events, 8 evaluation cases, 10 hotspots, 56 document chunks,
and 21 finding sources.

## Start the backend

```bash
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Interactive docs are at
`http://localhost:8000/docs`.

## Run tests

```bash
pytest
```

Tests use an isolated temporary SQLite database and never touch the development
database.

## Health endpoint

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"Civil Engineer AI Backend","phase":"2"}
```

## API route examples

All data routes are under the `/api/v1` prefix. The seeded project id is
`proj_brookside_meadows`.

```bash
# Projects
curl http://localhost:8000/api/v1/projects
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows

# Documents
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/documents
curl http://localhost:8000/api/v1/documents/doc_stormwater_report

# Checklist
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/checklist
curl http://localhost:8000/api/v1/checklist/chk_infiltration_testing

# Findings
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/findings
curl http://localhost:8000/api/v1/findings/find_infiltration_missing

# Audit events
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/audit-events

# Evaluation cases
curl http://localhost:8000/api/v1/evaluation-cases
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/evaluation-cases

# Hotspots
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/hotspots

# Document chunks
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/chunks
curl http://localhost:8000/api/v1/documents/doc_stormwater_report/chunks
curl http://localhost:8000/api/v1/chunks/chunk_swm_001

# Retrieval and source evidence
curl "http://localhost:8000/api/v1/projects/proj_brookside_meadows/search?query=infiltration%20testing"
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/checklist/chk_infiltration_testing/evidence
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/findings/find_infiltration_missing/evidence
curl http://localhost:8000/api/v1/findings/find_infiltration_missing/sources

# AI Review Assistant (mock provider by default)
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/ai-provider-mode
curl -X POST http://localhost:8000/api/v1/projects/proj_brookside_meadows/ai-review-runs
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/draft-findings
```

## AI provider configuration

The AI Review Assistant defaults to a deterministic mock provider. No API key is
required and live calls are disabled by default. Configure with environment
variables (see `.env.example`):

```env
AI_PROVIDER=mock
AI_MODEL=mock-review-v1
AI_ENABLE_LIVE_CALLS=false
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
PROMPT_VERSION=checklist_review_v1
```

To enable an optional live OpenAI provider: set `AI_PROVIDER=openai`,
`AI_ENABLE_LIVE_CALLS=true`, provide `OPENAI_API_KEY` (never commit it), set
`AI_MODEL`, and install the optional package with `pip install openai`. If the
live provider is unavailable, the service falls back to the mock provider.

## Project layout

```text
backend/
  app/
    main.py            FastAPI app, health endpoint, CORS, startup seeding
    core/
      config.py        Environment driven settings
      safety.py        Allowed status vocabulary and prohibited wording rules
    db/
      database.py      Engine, session factory, declarative base
      models.py        SQLAlchemy models
      seed.py          Canonical Brookside Meadows seed data and loader
      seed_evidence.py Seeded chunks, finding sources, retrieval queries
    schemas/           Pydantic response schemas
    services/          Read and retrieval service layer (no route logic in routes)
    api/
      routes.py        Aggregate v1 router
      v1/              One module per resource
  tests/               pytest suite
```

## Data source of truth

For Phase 2 the Python seed data in `app/db/seed.py` is the canonical runtime
source. The frontend TypeScript data under the repository `data` folder is kept
as a graceful fallback used only when the backend cannot be reached. The two are
aligned and describe the same Brookside Meadows fixture.
