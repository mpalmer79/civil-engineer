# Architecture

This is the canonical architecture reference for Civil Engineer AI. It replaces
the original long-form design brief and folds in the architecture overview, the
technical-decisions notes, and the per-feature and per-workflow specifications as
brief subsystem sections. The domain model is kept separately in
`docs/DOMAIN_MODEL.md`, and the route map in `docs/ROUTE_ARCHITECTURE.md`.

## Context

Civil Engineer AI is a two-service web application: a Next.js frontend and a
FastAPI backend. A reviewer works in the browser; the frontend never talks to the
FastAPI origin directly. Authenticated browser requests flow through a
same-origin backend-for-frontend proxy that attaches the session token
server-side. Live AI is disabled by default, so the system runs deterministically
on a mock provider with no external inference calls.

```
Browser (Next.js UI)
   |  same-origin fetch
Next.js server (BFF proxy, HttpOnly session cookie)
   |  validated /api/v1 paths, token attached server-side
FastAPI backend (services, SQLAlchemy, safety vocabulary)
   |
SQLite (dev/tests) or PostgreSQL (production)  +  local or S3-compatible storage
```

## Frontend

The frontend is Next.js App Router with TypeScript and Tailwind CSS.

- `app/`: routes and pages. Route groups organize the reviewer surfaces, the
  public demo, and the workspace and admin areas.
- `components/`: reusable UI, including shared loading, empty, and failure state
  components and the safety boundary banner.
- `lib/api/`: typed API modules. Wire types are generated from the FastAPI
  OpenAPI schema (`lib/api/generated/`), so frontend types stay aligned with
  backend schemas.
- `lib/server/`: server-only helpers, including the HttpOnly session handling.
- `lib/guide/`: the local project guide (see below).

The typed API client returns an explicit result for every request: success
carries the data and its source; failure carries a category (sign-in required,
forbidden, missing, validation, conflict, rate limited, timeout, backend
unavailable, invalid response) plus a correlation ID. Authenticated surfaces
render those states directly and never fall back to seeded data. Only public
Brookside demo surfaces may render the labeled repository fixture snapshot, and
they disclose it when they do.

## Backend

The backend is FastAPI with Pydantic schemas, SQLAlchemy models, and Alembic
migrations. It was decomposed from monolithic modules into cohesive packages:

- `app/db/models` package: SQLAlchemy models split by domain (identity, projects,
  documents, evidence, findings, checklists, cad, plans, workflow,
  review_packets, responses, response_packages, review_cycles, command_center,
  evaluation, billing, audit, plus shared bases).
- `app/core/vocab` package: the review-support safety vocabulary, split by domain
  (projects, documents, review, cad, checklists, responses, response_packages,
  review_cycles, workflow, dashboard, retrieval, storage, billing, auth,
  diagnostics, shared). `app/core/safety` enforces the vocabulary at the data
  layer.
- Service packages under `app/services`: one service (or service package) per
  review-support domain, including `cad`, `cad_intake_service`,
  `evidence_retrieval_service`, `review_cycle_service`, `command_center`, and
  `storage`, alongside the per-domain service modules.
- `app/db/seeds` package: the Brookside Meadows seed data and loaders (see
  `docs/REFERENCE_PROJECT.md`).
- `app/api/v1`: the versioned route table. `app/ai`: the provider abstraction and
  the deterministic mock provider. `app/schemas`: Pydantic request and response
  schemas.

## Data stores and file storage

- SQLite serves local development and tests; PostgreSQL is the production
  database, selected from `DATABASE_URL`. Schema changes are Alembic migrations.
- Uploaded files go through a storage provider abstraction: local disk for
  development, S3-compatible object storage for deployment. The database stores
  only safe metadata (provider, generated storage key, checksum, size,
  availability); storage credentials are backend-only and never reach the browser.
  Storage keys are generated and never derived from the raw filename, which
  prevents path traversal.

## Authentication and request flow

Authentication is local accounts with PBKDF2 password hashing and signed access
tokens. The browser never holds the token: sign-in stores it in an HttpOnly
cookie, and the same-origin proxy attaches it to backend calls server-side.
Session truth comes from a validated status endpoint. Every project-owned route
is gated by the access-control guards. Full detail is in `docs/SECURITY.md`.

## Subsystems

- PDF page indexing and evidence citations: digital PDFs are indexed page by page
  with pypdf; each page's embedded text becomes a searchable record, and findings
  cite the exact page and excerpt. No OCR; pages without a text layer are reported
  as extraction-unavailable.
- Checklists and rule packs: reusable stormwater rule packs seed project
  checklists; each item tracks its expected evidence and an evidence status
  (supported, missing, conflicting, unclear).
- Storage provider abstraction: the local and S3-compatible providers behind one
  interface, described above.
- Evidence retrieval and draft queue: deterministic ranked search over indexed
  page text, no live AI and no external vector service. Results are candidates
  that require reviewer confirmation and cite their source page.
- CAD and DXF intake: DXF metadata is parsed deterministically with ezdxf into
  layers, blocks, text, and reference candidates. A data-driven layer taxonomy,
  structured facility identities, a context-aware reference parser, and safe
  geometry bounds turn the raw parse into review-support records. DXF is the only
  supported CAD format.
- Applicant response matrix: applicant responses are tracked against the findings
  that prompted them, recorded for reviewer review and never as a final outcome.
- Response package and comment-letter workflow: reviewer-controlled response
  packages assemble the communication record; comment-letter drafts come from
  fixed deterministic templates with a fixed boundary statement. Issuance records
  a reviewer action, never an approval.
- Resubmittal collaboration workflow: resubmittal rounds carry items forward
  across review cycles; revision comparison uses extracted DXF metadata only.
- Reviewer dashboard and workload: operational review-support indicators only,
  every result filtered by access control; no count or status represents approval
  or resolution.
- Project traceability and handoff: an evidence traceability matrix links
  findings to source evidence, and the command center aggregates the whole review
  state for handoff.

## Observability

Public health (`/health`) and readiness (`/api/v1/readiness`) checks report safe
operational status only. Admin-gated diagnostics report whether configuration is
present, never a secret. A safe structured logger redacts secret-like and
path-like keys. Every proxied request carries a correlation ID. See
`docs/DEPLOYMENT.md`.

## The local project guide

`lib/guide` is a deterministic local project expert: it searches an allowlisted
knowledge catalog (`lib/guide/knowledge.ts`) with token-aware ranking, synonym
expansion, and page-context boosts, then composes answers from curated entries
with repository source references. Objective repository facts come from a
generated file (`lib/guide/generated/repo-facts.json`, regenerated through
`scripts/generate-guide-knowledge.mjs` and gated by
`scripts/check-guide-knowledge.mjs`). It calls no outside inference API and sends
no telemetry. See `docs/adr/0006-local-guide-knowledge-architecture.md`.

## External dependencies

- Runtime: Next.js, React, FastAPI, SQLAlchemy, Alembic, pypdf, ezdxf.
- Optional and off by default: a live AI provider (explicit configuration
  required), SMTP email, Stripe billing, S3-compatible object storage.

## Deployment

Two Railway services build from one repository. See `docs/DEPLOYMENT.md`.

## Failure modes

- Backend unreachable: authenticated surfaces render an explicit failure state
  with a correlation ID; public demo surfaces may render the labeled fixture.
- Invalid session: cookies are cleared and the user is prompted to sign in again.
- Parse failure on a DXF: reported as a technical parse failure, never an
  engineering failure.
- Scanned PDF with no text layer: reported as extraction-unavailable rather than
  silently skipped.

## Decision records

Architecture decisions are recorded in `docs/adr/`: canonical routes and shells
(0001), data-source boundaries (0002), secure session architecture (0003),
OpenAPI type generation (0004), backend domain decomposition (0005), local guide
knowledge architecture (0006), repository consolidation (0007), dependency
security policy (0008), documentation governance (0009), and evidence provenance
(0010).
