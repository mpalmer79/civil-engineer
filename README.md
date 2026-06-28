# Civil Engineer AI

Civil Engineer AI is a document-first, evidence-first, reviewer-controlled stormwater review-support platform. It helps a human reviewer upload and parse DXF files, index uploaded PDFs, search and organize evidence, apply checklist-driven review, organize findings and evidence, build review packets, track a plan review workflow, draft response packages, manage resubmittals across rounds, and see the whole review state in one reviewer command center.

It does not approve plans, certify compliance, verify CAD, validate design, declare safety, resolve issues, close issues, or replace a licensed Professional Engineer.

## Pilot release status

Civil Engineer AI is a pilot-ready prototype for early design-partner
conversations, not a production multi-tenant SaaS. The public Brookside Meadows
demo and `/guided-demo` run without a login, `/pilot` collects design-partner
requests, and a signed-in organization admin can review them at
`/admin/pilot-requests` and use the `/workspace` home. Billing is not active and
live AI is disabled by default. Every project-owned API route enforces tenant
access guards, with a guard-regression test to keep new routes covered.

- Run locally: see [Local development](#local-development).
- Run tests: `npm test` (frontend) and `pytest` from `backend/` (backend); see
  [Testing summary](#testing-summary).
- Verify the public demo: load `/` and `/guided-demo`; the demo reviews the
  seeded Brookside Meadows fixture.
- Verify the pilot flow: submit the `/pilot` form and confirm the honest success
  state; review it at `/admin/pilot-requests` as an organization admin.
- Limitations and steps: see `docs/RELEASE_READINESS.md` and
  `docs/PILOT_RELEASE_CHECKLIST.md`.

Capability wording follows `docs/SAAS_POSITIONING.md`: real DXF parsing (ezdxf)
and PDF text-layer indexing (pypdf), with no OCR, DWG, GIS, or vector search. A
human reviewer remains responsible for every review-support finding.

## Live demo

- https://civil-engineer.up.railway.app/

The demo reviews the Brookside Meadows fixture, a synthetic 47-lot subdivision in the Town of Hartwell with a green-and-gray stormwater treatment train and intentionally planted review issues. Brookside Meadows is a synthetic public demo fixture; it does not represent a real submission, permitting decision, approval, or compliance determination.

### Recommended demo path

New visitors should open **Start Here** (`/start-here`) for the fastest overview and a guided path, then **Guided Demo** (`/guided-demo`) to walk the reviewer journey. The recommended order through the Brookside Meadows sample project:

1. Review the sample project (`/projects/proj_brookside_meadows`)
2. Inspect uploaded documents
3. Open indexed PDF pages
4. View page-level evidence (evidence search)
5. Triage evidence candidates
6. Apply checklist review
7. Review findings
8. Record applicant responses (response matrix)
9. Track resubmittals
10. Build a reviewer response package
11. Preview a comment letter draft
12. View the reviewer dashboard and workload indicators

Search results and findings are candidates that require reviewer confirmation. Reviewer response packages are communication records, not approvals or issue closures.

For a recruiter or technical evaluator, the Start Here page also includes a five-minute review path, a deeper technical path, and a reviewer walkthrough checklist.

### Technical foundation

- Next.js frontend with a typed API client and a shared visual system
- FastAPI backend with a versioned review-support API
- SQLAlchemy data model for projects, documents, and review records
- PDF page indexing with per-page text extraction
- Page-level evidence citations and deterministic candidate retrieval (no live AI calls)
- Local authentication, organizations, roles, and per-project access control
- Object storage abstraction with credentials kept server-side
- Audit trail for reviewer actions and accesses
- Reviewer dashboard, workload metrics, and deployment diagnostics

### Intentionally out of scope

No live AI calls, no OCR, no DWG parsing or CAD geometry validation, no GIS integration, no enterprise single sign-on, no full applicant portal, and no final approval, certification, or compliance determination.

### Live-site navigation and discoverability

The primary navigation leads with the current product workflow: Home, Projects, Rule Packs, Organizations, Guided Demo, and Account/Login. The older Brookside Meadows demo modules (Project Dashboard, Documents, Checklist, Findings, Plan Sheets, CAD Review, Sheet Viewer, Review Packet, Workflow Board, Response Package, Review Cycles, CAD Intake, AI Review, Human Review, Audit, and Evaluation) remain available, grouped under a Demo modules menu and reachable from the Guided Demo. The homepage adds a Production foundation workflow section, a scannable What is live now summary of the delivered review-support capabilities, and a Public demo vs real project workflow explanation so a visitor can see that the public demo runs without an account while real project records require sign in and access control. A Start Here page and the Guided Demo are surfaced from the homepage hero and the footer so a first-time visitor or evaluator has an obvious entry point. Brookside Meadows remains the public guided demo fixture.

After a frontend redeploy, verify the live site against [docs/LIVE_SITE_VERIFICATION.md](docs/LIVE_SITE_VERIFICATION.md). A Next.js build can appear stale if Railway did not redeploy from the latest `main`; trigger a fresh frontend deploy and re-check.

## Production foundation progress

- Sprint 1: Real Project Intake and Persistent Review Records
- Sprint 2: PDF Page Indexing and Evidence Citations
- Sprint 3: Evidence Retrieval and Reviewer Draft Finding Queue
- Sprint 4: Checklist-Driven Evidence Review and Rule Pack Foundation
- Sprint 5: Real Authentication, Reviewer Roles, and Project Access Control
- Sprint 6: Durable Object Storage and Deployment-Ready File Persistence
- Sprint 7: Applicant Response Matrix and Resubmittal Collaboration Workflow
- Sprint 8: Reviewer Response Package Issuance and Comment Letter Workflow
- Sprint 9: Reviewer Dashboard, Workload Management, and Operational Metrics
- Sprint 10: Production Deployment Hardening, Environment Validation, and Observability

## Real-world product direction

Civil Engineer AI is moving from a controlled portfolio demo toward a real-world stormwater submission review-support system for small municipal engineering teams. Sprint 1 added Real Project Intake and Persistent Review Records: reviewers can create real project records, register or upload documents, create reviewer-owned review-support findings, attach basic evidence references, and inspect durable audit events. Brookside Meadows remains the seeded demo fixture.

Sprint 2 adds PDF page indexing and reviewer-selected evidence citations: uploaded PDFs can be indexed into page-level review records with extracted text, and reviewers can cite an exact page or section as evidence for a finding. Text extraction covers digital PDFs only. OCR and automated AI findings remain future work.

Sprint 3 adds local evidence retrieval and a reviewer draft finding queue. Reviewers can search indexed PDF page text deterministically, review citation candidates, save them to a queue, and promote a candidate into a reviewer draft finding with a page-level citation. Retrieval is deterministic and local. No live AI calls are added. Search results are candidates that require human confirmation, not conclusions, and the reviewer remains responsible for every finding.

Sprint 4 adds checklist-driven evidence review and a starter rule-pack foundation. Reviewers can apply a reusable stormwater rule pack to a project as a checklist, search indexed evidence against each checklist requirement, track reviewer-controlled checklist evidence status, link citations, and create draft findings from checklist items. Rule packs are review-support templates, not legal determinations and not compliance standards. Checklist evidence statuses require reviewer confirmation. No live AI calls are added.

Sprint 5 adds a local authentication and access-control foundation. Real users can sign in, belong to organizations, hold reviewer or admin roles, and access only the projects they are permitted to view or act on, with real audit attribution. The public Brookside Meadows demo remains available without an account. This is a local auth foundation, not enterprise single sign-on, and it protects review records rather than making engineering decisions.

Sprint 6 adds a durable storage foundation. Uploaded project files are managed through a storage provider abstraction, with local storage for development and S3-compatible object storage support for deployment. Storage credentials stay on the backend, file download is access controlled, and PDF indexing reads files through the storage layer. This is a file-persistence foundation and does not change the review-support boundary.

Sprint 7 adds an applicant response matrix and a resubmittal collaboration workflow. Reviewers can organize findings and checklist review items into a response matrix, record applicant responses for reviewer review, register resubmittal rounds, link documents to a round, and carry items forward across review rounds. An applicant response is recorded for reviewer review, never as proof, and carry-forward means continued review, not resolution. This is a reviewer-side collaboration-tracking foundation and does not change the review-support boundary.

Sprint 8 adds reviewer response package issuance and a comment letter draft workflow. Reviewers can assemble selected findings, checklist items, response matrix items, and citations into a controlled response package, generate a deterministic, reviewer-editable comment letter draft, preview the package, issue it as a reviewer communication record, and preserve a revision history with a durable audit trail. Package issuance records a reviewer communication only. It does not finalize a review outcome, resolve issues, or close issues, and it does not change the review-support boundary.

Sprint 9 adds a reviewer dashboard, workload management, and operational review-support metrics. Reviewers and organization admins can see project workload, pending reviewer actions, document indexing status, evidence and checklist review status, applicant response and resubmittal activity, and response package readiness across the projects they can access, with safe aging indicators, a reviewer queue, and a project assignment and review priority foundation. Every dashboard result is filtered by access control. Dashboard counts are operational indicators only. They do not represent a final review outcome or compliance determination, do not resolve issues, do not close issues, and do not change the review-support boundary.

Sprint 10 adds production deployment hardening, environment validation, and observability. The backend validates critical environment configuration and exposes safe health and readiness diagnostics, an admin-gated environment validation summary, storage configuration diagnostics, and a frontend integration check. A deployment status page and an updated backend connection banner give operators clearer operational status, and a live-site verification script checks the deployed frontend and backend. Diagnostics never expose secrets, credentials, database URLs, storage keys, signed URLs, or raw file system paths. They are operational readiness indicators only. They do not approve plans, certify compliance, validate design, declare safety, resolve issues, or close issues, and they do not change the review-support boundary.

Civil Engineer AI is a document-first, evidence-first, reviewer-controlled stormwater review-support platform. It does not approve plans, certify compliance, verify CAD, validate design, declare safety, resolve issues, close issues, or replace a licensed Professional Engineer. Real project records, page indexing, citations, evidence retrieval, checklist review, access control, durable storage, the applicant response matrix, the resubmittal workflow, response packages, comment letter drafts, the reviewer dashboard, and deployment diagnostics do not make final engineering decisions, do not resolve issues, and do not close issues. Enterprise SSO, OCR, malware scanning, live AI retrieval, jurisdiction-specific ordinance rule engines, an applicant portal, and external application performance monitoring are future roadmap items.

See the roadmap in [docs/REAL_WORLD_PRODUCT_ROADMAP.md](docs/REAL_WORLD_PRODUCT_ROADMAP.md), Sprint 1 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_1.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_1.md), Sprint 2 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_2.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_2.md) and [docs/PDF_PAGE_INDEXING_AND_EVIDENCE_CITATIONS.md](docs/PDF_PAGE_INDEXING_AND_EVIDENCE_CITATIONS.md), Sprint 3 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_3.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_3.md), [docs/EVIDENCE_RETRIEVAL_AND_DRAFT_QUEUE.md](docs/EVIDENCE_RETRIEVAL_AND_DRAFT_QUEUE.md), and [docs/API_EVIDENCE_RETRIEVAL.md](docs/API_EVIDENCE_RETRIEVAL.md), Sprint 4 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_4.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_4.md), [docs/CHECKLIST_RULE_PACK_FOUNDATION.md](docs/CHECKLIST_RULE_PACK_FOUNDATION.md), and [docs/API_CHECKLIST_REVIEW.md](docs/API_CHECKLIST_REVIEW.md), Sprint 5 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_5.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_5.md), [docs/AUTHENTICATION_AND_ACCESS_CONTROL.md](docs/AUTHENTICATION_AND_ACCESS_CONTROL.md), and [docs/API_AUTH_AND_ACCESS_CONTROL.md](docs/API_AUTH_AND_ACCESS_CONTROL.md), Sprint 6 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_6.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_6.md), [docs/STORAGE_PROVIDER_ABSTRACTION.md](docs/STORAGE_PROVIDER_ABSTRACTION.md), and [docs/API_FILE_STORAGE.md](docs/API_FILE_STORAGE.md), Sprint 7 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_7.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_7.md), [docs/APPLICANT_RESPONSE_MATRIX.md](docs/APPLICANT_RESPONSE_MATRIX.md), [docs/RESUBMITTAL_COLLABORATION_WORKFLOW.md](docs/RESUBMITTAL_COLLABORATION_WORKFLOW.md), and [docs/API_RESPONSE_MATRIX_AND_RESUBMITTALS.md](docs/API_RESPONSE_MATRIX_AND_RESUBMITTALS.md), and Sprint 8 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_8.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_8.md), [docs/RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md](docs/RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md), [docs/API_RESPONSE_PACKAGES.md](docs/API_RESPONSE_PACKAGES.md), and [docs/COMMENT_LETTER_TEMPLATE_BOUNDARY.md](docs/COMMENT_LETTER_TEMPLATE_BOUNDARY.md), and Sprint 9 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_9.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_9.md), [docs/REVIEWER_DASHBOARD_AND_WORKLOAD.md](docs/REVIEWER_DASHBOARD_AND_WORKLOAD.md), [docs/API_OPERATIONAL_METRICS.md](docs/API_OPERATIONAL_METRICS.md), and [docs/METRICS_BOUNDARY_AND_LIMITATIONS.md](docs/METRICS_BOUNDARY_AND_LIMITATIONS.md), and Sprint 10 in [docs/PRODUCTION_FOUNDATIONS_SPRINT_10.md](docs/PRODUCTION_FOUNDATIONS_SPRINT_10.md), [docs/DEPLOYMENT_HARDENING_AND_OBSERVABILITY.md](docs/DEPLOYMENT_HARDENING_AND_OBSERVABILITY.md), [docs/API_HEALTH_READINESS_AND_DIAGNOSTICS.md](docs/API_HEALTH_READINESS_AND_DIAGNOSTICS.md), [docs/ENVIRONMENT_VALIDATION.md](docs/ENVIRONMENT_VALIDATION.md), and [docs/LIVE_SITE_VERIFICATION.md](docs/LIVE_SITE_VERIFICATION.md). The reviewer dashboard lives under `/dashboard`, the reviewer queue under `/dashboard/queue`, the Projects pages under `/projects`, the deployment status page under `/deployment-status`, and sign-in lives under `/login`. Backend health is at `/health` and readiness at `/api/v1/readiness`.

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

This is a real-world foundation, not a full production release. The production foundation sprints have already added local authentication and role-based access control (Sprint 5) and durable object storage support (Sprint 6). Work that remains out of scope here includes enterprise single sign-on, a managed database with migrations, production security hardening, a full applicant portal, OCR, live AI calls, and real plan rendering. CAD scope beyond DXF metadata (DWG, Autodesk, Civil 3D, GIS, and computer vision) is also future work.

## Portfolio note

This project demonstrates a full-stack, domain-grounded application: a typed FastAPI backend with a clear service layer and a safety vocabulary that enforces professional boundaries, real DXF metadata parsing, a multi-round review workflow with evidence traceability and an audit trail, a Next.js frontend with a typed API client and graceful backend-unavailable fallback, and a clean two-service Railway deployment plan. It is built to read like a real plan review desk tool while staying explicit that it organizes review-support evidence and does not approve, certify, or validate engineering work.

## Documentation

- [`docs/PRODUCT_OVERVIEW.md`](docs/PRODUCT_OVERVIEW.md): the product by workflow and capability.
- [`docs/RAILWAY_DEPLOYMENT_GUIDE.md`](docs/RAILWAY_DEPLOYMENT_GUIDE.md): the Railway two-service deployment guide.
- [`docs/LIVE_SITE_VERIFICATION.md`](docs/LIVE_SITE_VERIFICATION.md): the post-deploy live-site verification checklist.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): system architecture.
- [`docs/CAD_INTEGRATION_ROADMAP.md`](docs/CAD_INTEGRATION_ROADMAP.md): the staged CAD integration path.
- [`docs/ROADMAP.md`](docs/ROADMAP.md): the product roadmap and detailed build history.
