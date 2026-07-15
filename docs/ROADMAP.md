# Roadmap

The single roadmap for Civil Engineer AI, structured by commitment level. It
folds in the former real-world product roadmap and CAD integration roadmap. The
historical phase-by-phase build record lives in `docs/archive/`.

Stormwater review is the starting point, not the endpoint. The same retrieval,
checklist, findings, review, audit, and evaluation backbone that powers
stormwater review is intended to carry later review modules.

## Committed (delivered and maintained)

- Reviewer-controlled stormwater review workflow: intake, PDF text-layer
  indexing (pypdf), DXF metadata parsing (ezdxf), evidence retrieval, checklists,
  findings, review packets, workflow board, response packages, resubmittal and
  revision comparison, and the reviewer command center.
- Local authentication, organizations, per-project access control, and a
  guard-regression test.
- HttpOnly cookie sessions through the Next.js backend-for-frontend proxy.
- Object storage abstraction (local and S3-compatible).
- Production database posture (SQLite for development, PostgreSQL for production)
  with Alembic migrations.
- Account lifecycle (password reset, team invitation), SMTP email behind a
  default noop provider, and Stripe billing scaffolding in test mode.
- Railway deployment configuration, CI gates, and the deterministic DXF proof
  harness.
- Structured, secret-safe logging with per-request correlation ids echoed on the
  response and written onto audit rows, a global safe-error handler, a
  configurable log level, and an inline PDF page cap. See `docs/OPERATIONS.md`
  and `docs/adr/0011-request-observability.md`.

## Planned (scoped, not yet built)

- Moving file and DXF processing off the request thread onto a background worker
  before enterprise-scale load. Today intake, PDF indexing, and DXF parsing run
  synchronously with size and page bounds; the worker migration removes the
  request-thread bound entirely.
- Raising the frontend coverage floors as the suite grows.

- Richer reviewer workload balancing and assignment on top of the existing
  assignment and priority foundation.
- Merging the demo review-packet builder onto backend-issued packages.
- Invoice and payment-failure handling and a customer portal link for self-serve
  plan changes, once live Stripe keys are configured.
- Additional usage-enforcement categories once their flows have dedicated
  user-entry guards.
- Routing the local demo analytics event names through a real analytics sink
  behind an explicit opt-in.

## Research (exploratory, unscheduled)

- Live AI retrieval assistance behind the same human review boundary, evidence
  bounded and citation required, staying off by default.
- Additional land-development review modules that mostly add checklist content,
  document types, and evaluation cases rather than new infrastructure: grading,
  utility coordination, roadway layout, construction phasing, comment-response,
  inspection closeout, RFI resolution, and cost and maintenance planning.
- Cross-cutting platform capabilities: evidence graphs, risk heatmaps,
  development-timeline tracking, and multi-role review.

## Deferred (evaluated, intentionally postponed)

These evidence-provenance fields were evaluated and deferred per
`docs/adr/0010-evidence-provenance.md`. Each is a database column addition with
migration, OpenAPI contract, and frontend type consequences, and no current
workflow reads it. When any is added, it arrives with an Alembic migration,
regenerated contract, frontend mapping, and an update to ADR 0010 in the same
change.

- `extraction_method` and `extractor_name` / `extractor_version` on citations.
  Deferred because they are derivable today: PDF citations come from the pypdf
  text-layer index and CAD references from the recorded parser identity.
- `source_entity_id` for DXF entity-level anchors.
- `manually_verified_at` and `manually_verified_by` on citations.
- Per-citation confidence scores. Deferred because retrieval ranking scores exist
  on results but are not persisted onto citations.

Also deferred: turning off the anonymous demo-reviewer fallback is a deployment
posture step, not a code change; denormalizing `organization_id` onto child
entities is deferred in favor of the per-route project guard plus the
guard-regression test.

## Out of scope

Deliberately excluded, with the boundary documented: DWG parsing, Autodesk and
Civil 3D integration, GIS integration and georeferencing, OCR, computer vision,
external vector search, enterprise single sign-on, and a full applicant-facing
portal. Live AI calls stay off by default. Nothing on this roadmap changes the
professional boundary: the product never approves plans, certifies compliance, or
replaces a licensed Professional Engineer.
