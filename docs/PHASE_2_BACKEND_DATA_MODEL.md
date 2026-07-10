# Phase 2: Backend and Data Model Foundation

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

**Product:** Civil Engineer AI: Stormwater Review Assistant
**Phase:** 2, Backend and Data Model Foundation

Phase 1 delivered a static Next.js prototype. Phase 2 turns that prototype into
a real full-stack foundation: a FastAPI backend, a structured data model,
Pydantic validation, a seed loader, a service layer, and frontend integration.

Civil Engineer AI is a review-support and evidence-organization system. It does
not approve plans, certify compliance, stamp drawings, or replace a licensed
Professional Engineer. Phase 2 carries that boundary into backend statuses,
validation, and tests.

## What Phase 2 adds

- A FastAPI backend with a `/health` endpoint and a versioned `/api/v1` read API.
- SQLAlchemy models for the core domain entities.
- SQLite local storage, with a connection setup that moves to PostgreSQL or
  Supabase by changing one environment variable.
- A canonical Python seed loader for the Brookside Meadows fixture.
- Pydantic schemas for every response.
- A service layer so routes stay thin and logic is testable.
- A frontend API client that reads from the backend, with a graceful fallback
  to local seed data.
- A pytest suite, including safety-vocabulary and human-review checks.

What Phase 2 deliberately excludes: live AI calls, embeddings, vector retrieval,
authentication, and deployment work.

## Backend architecture

```text
backend/app/
  main.py            FastAPI app, health endpoint, CORS, startup seeding
  core/
    config.py        Environment driven settings (DATABASE_URL, CORS_ORIGINS)
    safety.py        Allowed status vocabulary and prohibited wording rules
  db/
    database.py      Engine, session factory, declarative base
    models.py        SQLAlchemy models
    seed.py          Canonical Brookside Meadows seed data and loader
  schemas/           Pydantic response schemas (one module per resource)
  services/          Read service layer (one module per resource)
  api/
    routes.py        Aggregate v1 router
    v1/              One route module per resource
```

Request flow: a route depends on a database session, calls a service function,
and returns ORM objects that Pydantic serializes through `from_attributes`.
Routes contain no query logic; services own data access.

## API endpoints

Health:

- `GET /health` returns `{"status":"ok","service":"Civil Engineer AI Backend","phase":"2"}`

Data routes under `/api/v1` (seeded project id `proj_brookside_meadows`):

- `GET /projects`, `GET /projects/{project_id}`
- `GET /projects/{project_id}/documents`, `GET /documents/{document_id}`
- `GET /projects/{project_id}/checklist`, `GET /checklist/{checklist_item_id}`
- `GET /projects/{project_id}/findings`, `GET /findings/{finding_id}`
- `GET /projects/{project_id}/audit-events`
- `GET /evaluation-cases`, `GET /projects/{project_id}/evaluation-cases`
- `GET /projects/{project_id}/hotspots`

Unknown ids return a 404 with a clear detail message.

## Database tables

| Table | Purpose |
| --- | --- |
| `projects` | Project metadata, plus site conditions, improvements, and constraints as JSON |
| `documents` | The 19 submitted or referenced documents, with status and planted issues |
| `checklist_items` | The 19 stormwater checklist items and expected statuses |
| `findings` | The 10 expected review-support findings with related checklist items and documents |
| `audit_events` | The seeded audit trail |
| `evaluation_cases` | The 8 evaluation cases with seeded results as JSON |
| `hotspots` | The 10 homepage hotspots with map positions |

JSON columns hold arrays and nested values (for example site conditions,
supporting documents, and seeded evaluation results). These are easy to
normalize into separate tables in a later phase if needed. The schema is kept
clean and migration ready; Alembic can be added when the schema starts to
change in Phase 3.

## Seed data strategy

`backend/app/db/seed.py` is the canonical runtime source for Phase 2. It mirrors
the Phase 1 TypeScript seed data and preserves the fixture facts: 38.5 acres, 47
lots, 22 disturbed acres, 19 documents, 19 checklist items, 10 planted review
issues, and 8 evaluation cases.

The seed loader is idempotent. On startup the app seeds an empty database. The
`python -m app.db.seed` command reloads the fixture, replacing existing rows.

The frontend TypeScript data under the repository `data` folder is retained only
as a fallback used when the backend cannot be reached. The transition plan is:
Python seed data is the backend truth, the TypeScript data is the fallback, and
a later phase can remove the frontend dependency on static data once the backend
is always present.

## Safety vocabulary validation

`backend/app/core/safety.py` is the single source of truth for review status
values and prohibited final-decision language.

- `ALLOWED_REVIEW_STATUSES` lists every status the system may assign, none of
  which imply a final engineering decision.
- `HUMAN_REVIEW_STATUSES` lists the states that keep a finding under human
  control. Every seeded finding uses `requires_human_review`.
- `PROHIBITED_FINAL_DECISION_WORDS` lists language that must never appear as a
  status or conclusion, such as approved, certified, fully compliant, and safe.

Tests enforce these rules: checklist and finding statuses must be allowed and
clean, every finding must require human review, and the seeded evaluation cases
report a prohibited-wording count of zero. Explanatory prose may state that the
system does not approve plans; that is different from applying a prohibited word
as a status, which the tests prevent.

## Frontend integration strategy

`lib/api.ts` is a typed API client. Each function fetches from the backend at
`NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`) and maps the
snake_case payload into the camelCase shapes the Phase 1 components already use.
If the backend cannot be reached, the function returns local seed data.

The data-consuming pages are server components that fetch through this client.
The data-consuming components accept their data as props and default to the
static seed data, which keeps them backward compatible and easy to test. The net
effect: when the backend is up, the UI is backend-driven; when it is down, the
UI still renders.

## Tests and verification

The pytest suite covers:

1. Health endpoint returns ok.
2. Seed data loads Brookside Meadows.
3. Projects endpoint returns Brookside Meadows.
4. Documents endpoint returns 19 documents.
5. Checklist endpoint returns 19 checklist items.
6. Findings endpoint returns 10 findings.
7. Evaluation endpoint returns 8 cases.
8. Hotspots endpoint returns 10 hotspots.
9. Prohibited final-decision words are not used as statuses.
10. Every finding requires a human review status.

## CORS

CORS is configured from `CORS_ORIGINS` and defaults to the local Next.js dev
server origins `http://localhost:3000` and `http://127.0.0.1:3000`. The
permissive method and header settings are for local development only and should
be tightened before any non-local deployment, as noted in `main.py`.

## What remains out of scope for Phase 2

- Live AI calls and structured prompt execution
- Embeddings and vector retrieval (pgvector)
- Authentication and authorization
- Write endpoints and human review actions persisted through the API
- Deployment and hosting

## What Phase 3 should build next

Phase 3 is the retrieval layer: document chunking, embeddings, and
source-evidence search. Suggested groundwork from Phase 2 to build on:

- Add `document_chunks` and `finding_sources` tables to the data model.
- Introduce Alembic migrations once the schema begins to change.
- Add a retrieval service alongside the existing read services.
- Keep the safety vocabulary and human-review guarantees in place as findings
  begin to carry retrieved source citations.
