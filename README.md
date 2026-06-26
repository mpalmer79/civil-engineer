# Civil Engineer AI

Civil Engineer AI is a review-support platform for stormwater plan review that helps a human reviewer upload and parse DXF files, organize findings and evidence, build review packets, track a plan review workflow, draft response packages, manage resubmittals across rounds, and see the whole review state in one reviewer command center.

## Live demo

- Railway frontend demo: coming soon
- Railway backend health: coming soon

The demo reviews the Brookside Meadows fixture, a synthetic 47-lot subdivision in the Town of Hartwell with a green-and-gray stormwater treatment train and intentionally planted review issues.

## Real-world product direction

Civil Engineer AI is beginning to move from a controlled portfolio demo toward a real-world stormwater submission review-support system for small municipal engineering teams. The first real-world foundation is Real Project Intake and Persistent Review Records: reviewers can create real project records, register or upload documents, create reviewer-owned review-support findings, attach basic evidence references, and inspect durable audit events. Brookside Meadows remains the seeded demo fixture.

This direction is review-support only. Real project records do not approve plans, certify compliance, verify CAD, validate design, or make final engineering decisions. Full authentication, PDF parsing, page-level citations, jurisdiction rule packs, and an applicant portal are future roadmap items.

See the roadmap in [docs/REAL_WORLD_PRODUCT_ROADMAP.md](docs/REAL_WORLD_PRODUCT_ROADMAP.md) and the current sprint in [docs/PRODUCTION_FOUNDATIONS_SPRINT_1.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_1.md). The new Projects pages live under `/projects`.

### Checking the backend

The frontend reads the backend origin from `NEXT_PUBLIC_API_BASE_URL`. This must be the backend origin only, with no `/api/v1` path, because the frontend API modules append `/api/v1/...` themselves:

```
NEXT_PUBLIC_API_BASE_URL=https://your-backend-service.up.railway.app
```

To confirm a deployed backend is serving the review-support API, open these URLs against the backend origin:

- `/health` returns the health JSON (status, service name, version, demo mode).
- `/api/v1/projects/proj_brookside_meadows` returns the seeded Brookside Meadows project payload.

A `404` on the backend root `/` is not necessarily a failure. The backend does not serve a page at `/`; if `/health` and the `/api/v1` routes respond, the backend is working as expected.

## What the system does

Civil Engineer AI structures the work a reviewer does on a stormwater submission. It takes a real DXF file and seeded review data and turns them into organized, traceable, review-support evidence:

- Parses DXF metadata (layers, entities, blocks, text, and reference candidates) and compares references against a plan sheet index.
- Organizes findings, links each finding to its source evidence, and tracks every finding through human review.
- Assembles review packets, promotes items to a workflow board, drafts response packages, and tracks multi-round resubmittals with DXF metadata revision comparison.
- Aggregates the whole review state into a reviewer command center with attention items, health metrics, a timeline, readiness checks, and recommended next steps.

## Why it matters

Plan review is evidence work. Reviewers spend time finding what was submitted, comparing it against requirements, tracking what is missing or conflicting, and communicating it back to applicants across multiple rounds. Civil Engineer AI gives that work structure: every finding is traceable to its source, every status is a review-support status, and every reviewer action is recorded in an audit trail. It keeps a human reviewer in control and a licensed Professional Engineer responsible for any final decision.

## Core product workflow

1. Upload and parse DXF files.
2. Review extracted CAD metadata.
3. Organize findings.
4. Build review packets.
5. Track workflow items.
6. Generate draft response packages.
7. Manage resubmittals and revision comparisons.
8. View the reviewer command center.

## Key capabilities

- **Reviewer Command Center**: one dashboard aggregating attention items, health metrics, a timeline, readiness checks, and recommended next steps across every module.
- **Browser DXF Upload**: upload a DXF file with extension, size, content type, and readability validation, and safe generated storage names that prevent path traversal.
- **CAD Intake and Metadata Parsing**: parse layers, entities, blocks, text, and reference candidates from a real DXF file with the ezdxf library, with confidence labels and human-review flags.
- **Plan Sheet Viewer**: open a plan sheet with seeded hotspot annotations linked to plan consistency findings and references.
- **Review Packet Builder**: assemble documents, checklist items, findings, plan sheets, and audit evidence into a structured packet draft with a printable summary.
- **Workflow Board**: track review-support items through triage, follow-up, more information, reviewer checked, and ready for handoff.
- **Response Package Builder**: draft an external response grouped by topic with editable wording, an attachment checklist, and a human review sign-off checklist.
- **Resubmittal and Revision Comparison**: record resubmittals and compare extracted DXF metadata between rounds to surface added, removed, changed, unchanged, and carried-forward references.
- **Evidence Traceability**: every finding links back to its source evidence with document and page references in a traceability matrix.
- **Audit Trail**: reviewer actions and accesses are recorded as audit events so the decision history is preserved.

## Technical architecture

- **Frontend**: Next.js (App Router) with a TypeScript API client and Tailwind CSS.
- **Backend**: FastAPI with a versioned review-support API and SQLAlchemy models on SQLite.
- **DXF parsing**: Python DXF metadata parsing with the ezdxf library (a lightweight, pure-Python library). DXF is the only supported file type.
- **API client**: a typed TypeScript client that reads the backend base URL from an environment variable and falls back to seeded data when the backend is unavailable.
- **Deployment**: the backend and frontend deploy as two separate services in one Railway project.
- **Testing**: a backend pytest suite with a coverage gate and a frontend typecheck, lint, and vitest suite.

Live AI calls are disabled by default, so the demo runs deterministically with a mock provider and no API key.

## Professional boundary

Civil Engineer AI is a review-support and evidence-organization system. It does not:

- approve plans
- certify compliance
- verify CAD drawings
- validate engineering design
- stamp drawings or make final engineering decisions

A licensed Professional Engineer remains responsible for any final decision. Statuses such as ready for handoff and ready for human review describe review-support readiness, not approval. There is no action named approve.

## Repository structure

```text
civil-engineer/
  app/                 Next.js App Router pages (frontend)
  components/          React components
  lib/api/             TypeScript API client modules
  data/                Static seed data used as a graceful fallback
  public/              Static assets
  backend/
    app/
      main.py          FastAPI app, health endpoint, CORS, startup seeding
      core/            Settings and the review-support safety vocabulary
      db/              SQLAlchemy models, seed data, and loaders
      services/        Review-support services per capability
      api/v1/          One router module per resource
      cad_samples/     Bundled sample DXF fixtures
    tests/             pytest suite
    requirements.txt   Backend dependencies
    railway.json       Railway backend service configuration
  railway.json         Railway frontend service configuration
  docs/                Product overview, deployment guide, and design docs
```

## Local development

Backend (from the `backend` directory):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000` and the health check is at `http://localhost:8000/health`.

Frontend (from the repository root):

```bash
npm install
npm run dev
```

The frontend runs at `http://localhost:3000` and reads the backend base URL from `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`). Copy `.env.example` to `.env.local` to override it.

## Railway deployment plan

The app is prepared for one Railway project with two services. See [`docs/RAILWAY_DEPLOYMENT_GUIDE.md`](docs/RAILWAY_DEPLOYMENT_GUIDE.md) for full configuration details.

- **Backend service (FastAPI)**: root directory `backend`. Start command runs the FastAPI app and binds to the Railway port. Healthcheck path `/health`. Configured with `CORS_ORIGINS`, `FRONTEND_ORIGIN`, `CAD_UPLOAD_DIR`, `MAX_CAD_UPLOAD_BYTES` (or `CAD_MAX_UPLOAD_BYTES`), and `DEMO_MODE`.
- **Frontend service (Next.js)**: root directory the repository root. Build command runs the Next.js production build. Start command runs the Next.js production server bound to the Railway port. Configured with `NEXT_PUBLIC_API_BASE_URL` pointing at the deployed backend URL.

Upload storage note: uploaded DXF files are stored on the backend service file system under `CAD_UPLOAD_DIR`. This is demo-local storage and is not persistent across redeploys unless a Railway volume is mounted at that path.

## Testing summary

- Backend: a pytest suite with a coverage gate covering the API, the review-support services, DXF parsing, the safety vocabulary boundary, and configuration behavior.
- Frontend: a TypeScript typecheck, an ESLint lint pass, a vitest unit suite for the API client and components, and a production build.

## Future production work

This is a portfolio demo, not a production system. Production work that is intentionally out of scope here includes authentication and role-based access, a managed database with migrations, persistent object storage for uploads, production security hardening, and real document and plan rendering. CAD scope beyond DXF metadata (DWG, Autodesk, Civil 3D, GIS, OCR, and computer vision) is also future work.

## Portfolio note

This project demonstrates a full-stack, domain-grounded application: a typed FastAPI backend with a clear service layer and a safety vocabulary that enforces professional boundaries, real DXF metadata parsing, a multi-round review workflow with evidence traceability and an audit trail, a Next.js frontend with a typed API client and graceful backend-unavailable fallback, and a clean two-service Railway deployment plan. It is built to read like a real plan review desk tool while staying explicit that it organizes review-support evidence and does not approve, certify, or validate engineering work.

## Documentation

- [`docs/PRODUCT_OVERVIEW.md`](docs/PRODUCT_OVERVIEW.md): the product by workflow and capability.
- [`docs/RAILWAY_DEPLOYMENT_GUIDE.md`](docs/RAILWAY_DEPLOYMENT_GUIDE.md): the Railway two-service deployment guide.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): system architecture.
- [`docs/CAD_INTEGRATION_ROADMAP.md`](docs/CAD_INTEGRATION_ROADMAP.md): the staged CAD integration path.
- [`docs/ROADMAP.md`](docs/ROADMAP.md): the product roadmap and detailed build history.
