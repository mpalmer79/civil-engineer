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

## Current phase: Phase 5, Human Review Queue and Evaluation Scoring

Phase 5 adds the human review and evaluation scoring layer on top of the Phase 4
AI Review Assistant. It adds:

- A **human review queue** for AI draft findings
- **Persisted review actions**: accept, edit, reject, escalate, mark unclear, or
  request more information
- **Draft finding status transitions** driven by reviewer actions
- **Review action audit events** for every reviewer decision
- **Evaluation scoring** against the expected Brookside Meadows findings
- **Recall and precision** metrics
- **Citation validity rate** and **human review required rate**
- **Validation and safety failure tracking** with separate handling of failed
  drafts
- **Evaluation result storage** in the backend
- **Evaluation dashboard updates** that score a real AI review run
- Backend tests for review actions, status transitions, evaluation scoring, and
  audit events

Phase 5 keeps the professional boundary: there is no action called approve and
no status such as approved, certified, fully compliant, or safe. The system does
not provide production engineering approval, automated compliance, live
engineering design, final review decisions, or a replacement for a Professional
Engineer. Live AI calls are disabled by default, so the project runs without any
API key.

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
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): system architecture
- [`docs/RESEARCH_AND_SYSTEM_DESIGN.md`](docs/RESEARCH_AND_SYSTEM_DESIGN.md): research basis

---

## What Phase 5 proves

- The product manages a full review lifecycle: AI draft findings are routed
  through a human review queue where a reviewer accepts, edits, rejects,
  escalates, marks unclear, or requests more information, and every action is
  persisted with a status transition.
- The professional boundary holds in the review workflow: there is no approve
  action, failed drafts cannot be accepted, and edited text must still pass the
  prohibited-word safety check.
- Quality is measured: evaluation scoring compares draft findings against the
  expected findings and stores recall, precision, citation validity, and
  validation and safety failure counts.
- The decision history is preserved: every review action and evaluation run
  writes audit events with non-sensitive metadata.
- The project runs without any API key: the mock provider is the default and
  live calls are disabled.

## What comes next

- **Phase 6**: expansion modules that reuse the same retrieval, checklist,
  findings, human review, audit, and evaluation backbone to grow from a
  stormwater assistant into a broader land development review platform.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full plan.
