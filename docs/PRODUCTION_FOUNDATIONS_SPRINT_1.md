# Production Foundations Sprint 1: Real Project Intake and Persistent Review Records

This sprint adds the first real-world foundation layer on top of the seeded
Brookside Meadows demo. A reviewer can create a real project record, register or
upload documents, create reviewer-owned review-support findings, attach basic
evidence references, and inspect durable audit events. Brookside Meadows remains
a seeded demo fixture.

Everything added here is review-support only. Nothing approves plans, certifies
compliance, stamps drawings, verifies CAD, validates design, declares a project
safe, resolves or closes an issue, or makes a final engineering decision. There
is no action named approve.

## What was added

Backend:

- Production fields on the Project, Document, Finding, and AuditEvent models,
  all nullable or defaulted so the seeded demo fixture keeps working.
- A lightweight Actor model and a seeded demo reviewer identity for
  real-action attribution (placeholder for real authentication).
- A `real_intake_service` with create project, list and detail with counts,
  register document, upload document, create reviewer finding, and create
  evidence reference operations, each writing a durable audit event.
- Review-support vocabulary for project statuses, document processing statuses,
  reviewer finding statuses, evidence statuses, finding origins, and actor
  types, with prohibited final-decision wording rejected on user input.
- API routes under `/api/v1/projects` and `/api/v1/findings` (see
  [API_REAL_PROJECT_INTAKE.md](API_REAL_PROJECT_INTAKE.md)).

Frontend:

- A real project intake API client (`lib/api/realProjects.ts`).
- Pages: `/projects`, `/projects/new`, `/projects/[projectId]`,
  `/projects/[projectId]/documents`, `/projects/[projectId]/documents/register`,
  `/projects/[projectId]/findings`, `/projects/[projectId]/findings/new`, and
  `/projects/[projectId]/audit-events`.
- A Projects navigation link and a homepage "Real-world foundation now in
  progress" section.
- A source badge distinguishing the demo fixture from user-created records.

## What remains demo-only

- Brookside Meadows and all existing demo pages (Project, Documents, Checklist,
  Findings, Guided Demo, CAD Intake, CAD Review, Sheet Viewer, Review Packet,
  Workflow Board, Response Package, Review Cycles, Project Dashboard, Audit,
  Evaluation) are unchanged.
- The seeded documents, findings, chunks, plan sheets, and CAD intake data
  remain demo fixtures (source_mode demo_fixture).

## What remains out of scope

Live AI calls, single sign-on, full authentication and roles, tenant
separation, DWG parsing, OCR, GIS, Bluebeam, applicant portal functionality,
automated engineering calculations, and geometry or design validation are out of
scope for this sprint. PDF parsing and page-level citations are Phase 2.

## How Brookside Meadows demo mode coexists with real project intake

Projects, documents, and findings carry a `source_mode`. The seeded Brookside
Meadows fixture is `demo_fixture`; records created through the new intake
endpoints are `user_created`, `user_registered`, or `user_uploaded`. The
projects list shows both, with a source badge. Listing can be filtered by
`source_mode` (`all`, `demo_fixture`, or `user_created`).

## How to test the new workflow locally

1. Start the backend: from `backend/`, run `uvicorn app.main:app --reload`.
2. Start the frontend: from the repository root, run `npm run dev`.
3. Open `/projects`, click New project, and create a project record.
4. On the project page, register a document or upload a file, then create a
   review-support finding.
5. Open Audit events to see project_created, document_registered or
   document_uploaded, and finding_created events with reviewer attribution.

## Backend endpoints added

- `GET /api/v1/projects` (now includes counts and supports `source_mode`)
- `POST /api/v1/projects`
- `GET /api/v1/projects/{project_id}` (now includes counts and metadata)
- `POST /api/v1/projects/{project_id}/documents/register`
- `POST /api/v1/projects/{project_id}/documents/upload`
- `POST /api/v1/projects/{project_id}/findings`
- `POST /api/v1/findings/{finding_id}/evidence-references`
- `GET /api/v1/findings/{finding_id}/evidence-references`

Existing routes (documents list, findings list, audit events list, health, and
all Brookside Meadows demo routes) are unchanged.

## Frontend pages added

- `/projects`, `/projects/new`, `/projects/[projectId]`,
  `/projects/[projectId]/documents`, `/projects/[projectId]/documents/register`,
  `/projects/[projectId]/findings`, `/projects/[projectId]/findings/new`,
  `/projects/[projectId]/audit-events`.

## Known limitations

- The demo reviewer identity is a placeholder; there is no real authentication
  yet, so any caller acts as the demo reviewer.
- Uploaded files are stored on the local file system and are not parsed. PDF
  ingestion and page-level citations are Phase 2.
- Evidence references are a basic review-support placeholder, not a citation
  engine; real document chunks for uploaded files do not exist yet.
- The prototype has no database migrations. New columns are created for fresh
  databases; an existing development SQLite file from a previous phase should be
  recreated to pick up the new columns.

## Recommended next sprint

Production Foundations Sprint 2: PDF Page Indexing and Evidence Citations.
Real file upload landed in this sprint, so the next step is ingesting uploaded
PDFs into page-indexed chunks and grounding evidence references in real pages.
