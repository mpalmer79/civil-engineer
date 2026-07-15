# Civil Engineer AI

Civil Engineer AI is a document-first, evidence-first, reviewer-controlled
stormwater review-support platform. It helps a human reviewer upload and parse
DXF files, index uploaded PDFs, search and organize evidence, apply
checklist-driven review, organize findings against their source citations, build
review packets, track a plan review workflow, draft response packages, manage
resubmittals across rounds, and see the whole review state in one reviewer
command center.

It does not approve plans, certify compliance, verify CAD, validate design,
declare safety, resolve issues, close issues, or replace a licensed Professional
Engineer. Every output is review-support material for a human decision maker.

## Intended users

Municipal reviewers, civil engineering reviewers, internal QA reviewers, and
project managers who organize a stormwater submission, track findings across
review rounds, and prepare communication back to an applicant while keeping every
step traceable and under human control. Small and mid-sized civil and AEC firms
running pre-submittal QA are the primary audience.

## Core capabilities

- Browser DXF upload with validated intake and real ezdxf metadata parsing.
- PDF text-layer indexing (pypdf) with page-level evidence citations.
- Deterministic evidence retrieval that cites its source page.
- Checklist-driven review against reusable stormwater rule packs.
- Findings linked to evidence, applicant response tracking, and resubmittal and
  revision comparison across rounds.
- Reviewer-controlled response packages and a reviewer command center.

## Safety and decision boundary

The system organizes evidence and drafts review-support findings. It never
approves plans, certifies compliance, stamps drawings, declares a project safe,
or makes a final engineering decision, and there is no action named approve. A
central safety vocabulary in the backend and content tests in the frontend keep
statuses within review-support language. See [docs/SECURITY.md](docs/SECURITY.md).

## Architecture summary

A Next.js frontend and a FastAPI backend deploy as two services. Authenticated
browser requests flow through a same-origin backend-for-frontend proxy that
attaches an HttpOnly session token server-side. The backend uses SQLAlchemy
models, Alembic migrations, and a per-domain safety vocabulary; SQLite serves
local development and tests while PostgreSQL is the production database. Live AI
is disabled by default. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Live demo

Live demo: https://civil-engineer.up.railway.app/

Recommended demo path:

1. Open `/start-here` for the technical overview and evaluation paths.
2. Open `/guided-demo` to walk the reviewer journey over the synthetic Brookside
   Meadows reference project.
3. Open a project or a review packet to see the evidence detail, where every
   finding links to source citations and applicant responses are tracked across
   resubmittal rounds.

The demo runs on the synthetic Brookside Meadows reference project. See
[docs/REFERENCE_PROJECT.md](docs/REFERENCE_PROJECT.md).

## Local development

```bash
# Backend (from backend/)
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (from the repository root)
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` to the backend origin (default
`http://localhost:8000`).

## Validation commands

```bash
npm run typecheck
npm run lint
npm run check:content
npm run check:guide
npm test
npm run build
cd backend && pytest
```

See [docs/TESTING.md](docs/TESTING.md).

## Deployment summary

Deployment targets Railway as two services. Set one frontend variable to the
backend origin only, with no `/api/v1` path:

```
NEXT_PUBLIC_API_BASE_URL=https://your-backend-service.up.railway.app
```

Verify the backend with `/health` and
`/api/v1/projects/proj_brookside_meadows`. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [docs/OPERATIONS.md](docs/OPERATIONS.md).

## Documentation

- [docs/PRODUCT.md](docs/PRODUCT.md): product overview and capability boundary.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): system architecture.
- [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md): the review-support domain model.
- [docs/SECURITY.md](docs/SECURITY.md): security and the professional boundary.
- [docs/OPERATIONS.md](docs/OPERATIONS.md): release, pilot, billing, and email.
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): deployment and the database.
- [docs/TESTING.md](docs/TESTING.md): tests and release gates.
- [docs/API.md](docs/API.md): API surfaces and the OpenAPI contract.
- [docs/DXF_VALIDATION.md](docs/DXF_VALIDATION.md): the DXF proof of concept.
- [docs/REFERENCE_PROJECT.md](docs/REFERENCE_PROJECT.md): Brookside Meadows.
- [docs/ROADMAP.md](docs/ROADMAP.md): committed, planned, and out-of-scope work.
- [docs/README.md](docs/README.md): the full documentation map.

## Technical foundation

Next.js App Router with TypeScript and Tailwind CSS on the frontend; FastAPI with
SQLAlchemy, Alembic, pypdf, and ezdxf on the backend. Wire types are generated
from the FastAPI OpenAPI schema, and CI runs typecheck, lint, unit and content
tests, a content integrity gate, dependency audits, the production build, the API
contract check, the DXF proof harness, and a Playwright and accessibility suite.

## Intentionally out of scope

DWG parsing, Autodesk and Civil 3D integration, GIS integration, OCR, computer
vision, external vector search, enterprise single sign-on, and a full
applicant-facing portal. Live AI calls stay disabled by default.
