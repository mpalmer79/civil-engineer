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

## Current phase: Phase 7, Plan Sheet Viewer and Sheet Hotspot Review

Phase 7 adds a reviewer-facing plan sheet viewer on top of the Phase 6 plan
sheet and CAD-aware foundation. It adds plan sheet intelligence in a viewer,
not real PDF or CAD parsing. It adds:

- A **plan sheet viewer** with a synthetic sheet preview and a numbered hotspot
  overlay
- **Seeded sheet hotspots** placed with percentage coordinates and linked to
  plan references, CAD-aware metadata, plan consistency findings, documents, and
  checklist items
- A **sheet viewer context** endpoint that bundles a sheet with its hotspots and
  related evidence
- **Plan consistency review actions** (needs follow up, reviewer confirmed, not
  applicable, needs more information), persisted with status transitions
- **Audit events** for viewer context requests, hotspot inspection, and plan
  review actions
- Backend tests for the hotspots, the viewer context, and the review actions

Phase 7 keeps the professional boundary: the sheet preview and hotspots are
seeded review-support metadata, not parsed PDF, DWG, DXF, or Autodesk data, and
the system does not verify CAD, validate the design, certify compliance, or make
final engineering decisions. There is no action called approve and no status
such as approved, certified, fully compliant, or safe. Live AI calls are
disabled by default, so the project runs without any API key.

Earlier phases established the product foundation:

- Phase 0: research, domain model, and the Brookside Meadows project story
- Phase 1: a static Next.js prototype driven by seed data
- Phase 2: a FastAPI backend, SQLite database, SQLAlchemy models, seeded data,
  API endpoints, tests, and frontend integration
- Phase 3: document chunks, finding sources, and keyword retrieval with
  evidence display
- Phase 4: a controlled AI review run workflow with a mock provider, evidence
  first prompts, strict JSON validation, safety and citation checks, and
  mandatory human review for every draft finding
- Phase 5: a persisted human review queue, reviewer actions with status
  transitions, and evaluation scoring of AI draft findings against the expected
  Brookside Meadows findings
- Phase 6: a plan sheet index, CAD-aware civil feature metadata, plan
  references, missing sheet detection, and plan consistency findings, with Plan
  Sheets and CAD Review pages

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
they fall back to the local seed data so the app still works. Core project pages
include static fallback data, but Phase 3 source evidence and Phase 4 AI draft
findings are backend-canonical. If the backend is not running, evidence and AI
review panels show a status note instead of duplicated or stale data.

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
| `/plan-sheets` | Plan Sheets | The Brookside Meadows plan sheet index with revisions and missing sheet detection |
| `/cad-review` | CAD Review | CAD-aware feature metadata, plan references, and plan consistency findings |
| `/ai-review` | AI Review Assistant | Run a controlled AI review and view draft findings and validation failures |
| `/human-review` | Human Review queue | Record reviewer actions and status transitions on draft findings |
| `/audit` | Audit trail | Seeded, traceable review history |
| `/evaluation` | Evaluation dashboard | Score a review run with recall, precision, and citation metrics |

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
- `GET /api/v1/projects/{project_id}/chunks` and `GET /api/v1/documents/{document_id}/chunks` and `GET /api/v1/chunks/{chunk_id}`
- `GET /api/v1/projects/{project_id}/search?query=...`
- `GET /api/v1/projects/{project_id}/checklist/{checklist_item_id}/evidence`
- `GET /api/v1/projects/{project_id}/findings/{finding_id}/evidence`
- `GET /api/v1/findings/{finding_id}/sources`
- `POST /api/v1/projects/{project_id}/ai-review-runs` and `GET /api/v1/projects/{project_id}/ai-review-runs`
- `GET /api/v1/ai-review-runs/{review_run_id}` and `GET /api/v1/ai-review-runs/{review_run_id}/draft-findings`
- `GET /api/v1/projects/{project_id}/draft-findings` and `GET /api/v1/draft-findings/{draft_finding_id}`
- `GET /api/v1/projects/{project_id}/ai-provider-mode`
- `GET /api/v1/projects/{project_id}/human-review-queue`
- `POST /api/v1/draft-findings/{draft_finding_id}/review-actions` and `GET /api/v1/draft-findings/{draft_finding_id}/review-actions`
- `GET /api/v1/projects/{project_id}/review-actions`
- `POST /api/v1/ai-review-runs/{review_run_id}/evaluate` and `GET /api/v1/ai-review-runs/{review_run_id}/evaluation`
- `GET /api/v1/projects/{project_id}/ai-evaluation-results` and `GET /api/v1/ai-evaluation-results/{evaluation_result_id}`
- `GET /api/v1/projects/{project_id}/plan-sheets` and `GET /api/v1/projects/{project_id}/plan-sheets/summary` and `GET /api/v1/plan-sheets/{sheet_id}`
- `GET /api/v1/projects/{project_id}/cad-metadata` (optional `?entity_type=`) and `GET /api/v1/plan-sheets/{sheet_id}/cad-metadata`
- `GET /api/v1/projects/{project_id}/plan-references` and `GET /api/v1/projects/{project_id}/plan-references/inconsistencies`
- `POST /api/v1/projects/{project_id}/plan-consistency-check` and `GET /api/v1/projects/{project_id}/plan-consistency-findings`
- `GET /api/v1/plan-consistency-findings/{plan_finding_id}`
- `GET /api/v1/projects/{project_id}/sheet-hotspots` and `GET /api/v1/projects/{project_id}/sheet-hotspots/summary`
- `GET /api/v1/plan-sheets/{sheet_id}/sheet-hotspots` and `GET /api/v1/plan-sheets/{sheet_id}/viewer-context` and `GET /api/v1/sheet-hotspots/{hotspot_id}`
- `POST /api/v1/plan-consistency-findings/{plan_finding_id}/review-actions` and `GET /api/v1/plan-consistency-findings/{plan_finding_id}/review-actions`
- `GET /api/v1/projects/{project_id}/plan-consistency-review-actions`

The frontend adds a `/sheet-viewer` page (sheet picker) and a
`/sheet-viewer/{sheetId}` page (the plan sheet viewer with hotspots and review
panels), alongside the existing `/plan-sheets` and `/cad-review` pages.

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
- [`docs/PHASE_3_RETRIEVAL_FOUNDATION.md`](docs/PHASE_3_RETRIEVAL_FOUNDATION.md): Phase 3 evidence and retrieval
- [`docs/PHASE_4_AI_REVIEW_ASSISTANT.md`](docs/PHASE_4_AI_REVIEW_ASSISTANT.md): Phase 4 AI review workflow
- [`docs/PHASE_5_HUMAN_REVIEW_AND_EVALUATION.md`](docs/PHASE_5_HUMAN_REVIEW_AND_EVALUATION.md): Phase 5 human review and evaluation scoring
- [`docs/PHASE_6_PLAN_SHEET_CAD_FOUNDATION.md`](docs/PHASE_6_PLAN_SHEET_CAD_FOUNDATION.md): Phase 6 plan sheet and CAD-aware review foundation
- [`docs/PHASE_7_PLAN_SHEET_VIEWER.md`](docs/PHASE_7_PLAN_SHEET_VIEWER.md): Phase 7 plan sheet viewer and sheet hotspot review
- [`docs/CAD_INTEGRATION_ROADMAP.md`](docs/CAD_INTEGRATION_ROADMAP.md): staged CAD integration path
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): system architecture
- [`docs/RESEARCH_AND_SYSTEM_DESIGN.md`](docs/RESEARCH_AND_SYSTEM_DESIGN.md): research basis

---

## What Phase 7 proves

- The product gives reviewers spatial context: a reviewer can open a plan sheet,
  see numbered hotspots over a synthetic preview, and inspect the connected plan
  references, CAD-aware metadata, documents, checklist items, and plan
  consistency findings in place.
- The review lifecycle extends to plan findings: a reviewer records needs follow
  up, reviewer confirmed, not applicable, or needs more information on a plan
  consistency finding, persisted with a status transition.
- The professional boundary holds: the sheet preview and hotspots are seeded
  review-support metadata, not parsed PDF, DWG, DXF, or Autodesk data, and the
  system does not verify CAD, validate the design, or approve plans. There is no
  action called approve.
- The decision history is preserved: viewer context requests, hotspot
  inspection, and plan review actions all write audit events.
- The project runs without any API key: the mock provider is the default and
  live calls are disabled.

## What comes next

- **Phase 8**: DXF metadata extraction or structured plan exports that populate
  the existing CAD-aware metadata, with real sheet rendering and Autodesk viewer
  exploration as later stages.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) and
[`docs/CAD_INTEGRATION_ROADMAP.md`](docs/CAD_INTEGRATION_ROADMAP.md) for the full
plan.
