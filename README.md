# Civil Engineer AI: Stormwater Review Assistant

Civil Engineer AI is a portfolio GenAI system that assists stormwater and
site-plan review using document evidence, checklist validation, risk flagging,
human review, audit logging, and evaluation tracking.

It is a **review-support and evidence-organization** system for land development
workflows. It is **not** a licensed engineering tool and does not replace
professional engineering judgment.

> **Professional boundary.** Civil Engineer AI assists review. It does not
> approve plans, certify compliance, stamp or seal drawings, replace a licensed
> Professional Engineer, or make final safety determinations. Every finding is a
> review-support issue that needs reviewer confirmation.

---

## Current phase: Phase 2, Backend and Data Model Foundation

Phase 2 turns the Phase 1 static prototype into a real full-stack foundation.
It adds:

- A **FastAPI** backend with a versioned read API
- A **SQLite** local database (with a clean path to PostgreSQL or Supabase)
- A **SQLAlchemy** data model aligned with the Phase 0 domain model
- **Seeded Brookside Meadows** data loaded into the database
- **API endpoints** for projects, documents, checklist items, findings, audit
  events, evaluation cases, and hotspots
- **Backend tests** with pytest, including safety-vocabulary checks
- **Frontend API integration**: pages fetch from the backend when it is
  available and fall back to local seed data when it is not

Phase 2 does not add live AI calls, embeddings, vector retrieval, or
authentication. Those are planned for later phases.

The reviewed fixture remains **Brookside Meadows**: a 47-lot single-family
subdivision in the Town of Hartwell with a green-and-gray stormwater treatment
train and ten intentionally planted review issues.

![Brookside Meadows development map](public/development.png)

---

## Getting started

### Frontend (Next.js)

```bash
npm install
npm run dev        # http://localhost:3000
npm run build
npm run typecheck
```

Set the backend URL for the frontend with an environment variable:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

When the backend is reachable, pages render live data from it. When it is not,
they fall back to the local seed data so the app still works.

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.db.seed            # load the Brookside Meadows fixture
uvicorn app.main:app --reload    # http://localhost:8000
pytest
```

See [`backend/README.md`](backend/README.md) for full backend setup and route
examples.

---

## Frontend routes

| Route | Page | Purpose |
| --- | --- | --- |
| `/` | Home | Hero map, metrics, how it works, professional boundary, future modules |
| `/project` | Project dashboard | Brookside Meadows summary, site conditions, improvements, constraints |
| `/documents` | Document library | The seeded submission package with status and planted issues |
| `/checklist` | Stormwater checklist | 19 structured review items with expected statuses |
| `/findings` | Findings | The 10 expected review-support findings |
| `/audit` | Audit trail | Seeded, traceable review history |
| `/evaluation` | Evaluation dashboard | 8 evaluation cases with recall and citation metrics |

## Backend endpoints

All data routes use the `/api/v1` prefix. Seeded project id:
`proj_brookside_meadows`.

- `GET /health`
- `GET /api/v1/projects` and `GET /api/v1/projects/{project_id}`
- `GET /api/v1/projects/{project_id}/documents` and `GET /api/v1/documents/{document_id}`
- `GET /api/v1/projects/{project_id}/checklist` and `GET /api/v1/checklist/{checklist_item_id}`
- `GET /api/v1/projects/{project_id}/findings` and `GET /api/v1/findings/{finding_id}`
- `GET /api/v1/projects/{project_id}/audit-events`
- `GET /api/v1/evaluation-cases` and `GET /api/v1/projects/{project_id}/evaluation-cases`
- `GET /api/v1/projects/{project_id}/hotspots`

---

## Project structure

```text
civil-engineer/
  app/              Next.js App Router pages
  components/       Reusable UI components
  data/             TypeScript seed data (frontend fallback)
  lib/              Frontend API client
  public/
    development.png Hero and interactive map base image
  backend/          FastAPI backend, SQLAlchemy models, seed data, tests
  docs/             Phase 0 foundation, hotspot plan, Phase 2 backend notes
```

---

## Tech stack

- **Next.js 14** (App Router) and **React 18**, **TypeScript** (strict)
- **Tailwind CSS**
- **FastAPI**, **Pydantic**, **SQLAlchemy**, **SQLite** for local storage
- **pytest** for backend tests

---

## Documentation

- [`docs/PHASE_0_FOUNDATION.md`](docs/PHASE_0_FOUNDATION.md): product definition and boundaries
- [`docs/BROOKSIDE_MEADOWS_PROJECT_STORY.md`](docs/BROOKSIDE_MEADOWS_PROJECT_STORY.md): the review fixture
- [`docs/DOMAIN_MODEL.md`](docs/DOMAIN_MODEL.md): core entities and ER diagram
- [`docs/V1_SCOPE.md`](docs/V1_SCOPE.md): in and out of scope and success criteria
- [`docs/ROADMAP.md`](docs/ROADMAP.md): staged path from foundation to platform
- [`docs/SEED_DATA_PLAN.md`](docs/SEED_DATA_PLAN.md): seed-ready data
- [`docs/HOMEPAGE_HOTSPOT_PLAN.md`](docs/HOMEPAGE_HOTSPOT_PLAN.md): interactive map plan
- [`docs/PHASE_2_BACKEND_DATA_MODEL.md`](docs/PHASE_2_BACKEND_DATA_MODEL.md): Phase 2 backend and data model
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): system architecture
- [`docs/RESEARCH_AND_SYSTEM_DESIGN.md`](docs/RESEARCH_AND_SYSTEM_DESIGN.md): research basis

---

## What Phase 2 proves

- The product is structurally real: a backend, a data model, validation, seed
  loading, and a service layer, not only a static mockup.
- The professional boundary is enforced in code through a central status
  vocabulary and prohibited-wording checks, verified by tests.
- The same Brookside Meadows fixture now drives both the API and the UI.

## What comes next

- **Phase 3**: document chunking, embeddings, and source-evidence retrieval.
- **Phase 4**: the AI review assistant (structured prompts, JSON validation,
  safety checks, human review required for every finding).
- **Phase 5**: the live evaluation harness.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full plan.
