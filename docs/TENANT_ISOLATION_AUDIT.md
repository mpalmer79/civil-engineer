# Tenant Isolation Audit

Phase 2A audit of the existing organization and project access patterns, ahead of
deeper multi-tenant SaaS work. This is an honest snapshot of what is enforced
today, what was hardened in this pass, and what remains before production
multi-tenancy. It does not claim production-grade tenant isolation.

## Scope

Backend access control for project-scoped data: the FastAPI routers under
`backend/app/api/v1`, the access-control service, and the auth and project
models. Frontend assumptions about the public demo project are noted where they
matter.

## Current models involved

Defined in `backend/app/db/models.py`:

- `UserAccount`: local user with `password_hash`, `is_active`, `is_demo_user`.
- `Organization`: a tenant. `OrganizationMembership` links a user to an
  organization with a `role` (for example `reviewer`, `org_admin`).
- `Project`: carries the tenancy fields `organization_id`, `created_by_user_id`,
  `visibility_mode` (`controlled` or `demo_public`), and `demo_public`.
- `ProjectAccess`: explicit per-project grants, either to a `user_id` or an
  `organization_id`, with an `access_level` (`project_admin`, `senior_reviewer`,
  `reviewer`, `read_only`).
- Child entities (documents, findings, evidence, traceability rows, workflow
  items, review packets, CAD records) reference `project_id` only. They have no
  `organization_id` of their own, so their isolation depends entirely on the
  project access check being applied before they are read or written.

## Current access-control pattern

Defined in `backend/app/services/access_control_service.py`:

- `get_optional_user` resolves the signed-in user from a Bearer token, or `None`.
  `get_current_user` requires a user and raises 401 otherwise.
- `effective_access_level(db, project_id, user)` returns the strongest active
  access level from direct user grants, organization grants, and implicit
  `org_admin` to `project_admin` promotion, or `None`.
- `require_project_read`, `require_project_reviewer`, and `require_project_admin`
  are the canonical guards. They resolve the project (404 if missing), allow the
  public demo exception where configured, fall back to a demo reviewer identity
  when demo mode permits, and otherwise require the appropriate access level
  (401 when anonymous and login is required, 403 when the user lacks access).

The canonical, correct route pattern (see `findings.py`, `documents.py`,
`evidence_retrieval.py`, `dashboard.py`, `checklist_review.py`) is:

```python
def handler(project_id: str,
            user: models.UserAccount | None = Depends(get_optional_user),
            db: Session = Depends(get_db)):
    require_project_read(db, project_id, user)   # or reviewer / admin
    ...
```

## Public demo exception behavior

The Brookside Meadows sample project (`proj_brookside_meadows`) is marked
`demo_public = True` / `visibility_mode = "demo_public"` by
`access_control_service.ensure_auth_seed`. When `AUTH_ALLOW_PUBLIC_DEMO` is set,
`require_project_read` allows anonymous read of that project so the no-login demo
keeps working. This exception is intentional and scoped to the demo project. It
is not a model for tenant-owned customer data, which should always require a
signed-in member.

Relevant settings (`backend/app/core/config.py`): `AUTH_DEMO_MODE`,
`AUTH_ALLOW_PUBLIC_DEMO`, `AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS`.

## Routes reviewed and enforcement status

Verified by inspecting each router for guard usage. As of Phase 2B, every
project-owned router enforces the project access guards.

Enforced (call `require_project_*` or `get_current_user`):

- Phase 2A: `projects.py`, `documents.py`, `findings.py`,
  `evidence_retrieval.py`, `dashboard.py`, `checklist_review.py`, `auth.py`,
  `file_storage.py`, `response_matrix.py`, `reviewer_response_packages.py`,
  `pdf_evidence.py` (mutations), `chunks.py` (mutation), and `traceability.py`.
- Phase 2B (this pass): `cad_intake.py`, `cad_metadata.py`, `workflow.py`,
  `review_packets.py`, `plan_consistency.py`, `command_center.py`,
  `plan_sheets.py`, `plan_sheet_hotspots.py`, `plan_references.py`,
  `hotspots.py`, `checklist.py`, `retrieval.py`, `chunks.py` (reads + raw ids),
  `ai_review.py`, `human_review.py`, `evaluation.py`, `pdf_evidence.py`
  (reads + mutations), `response_packages.py`, `review_cycle.py`, and
  `audit.py`.

Intentionally not project-scoped (no per-tenant data, so no project guard):

- `GET /cad-upload-limits` (static upload policy), `GET /evaluation-cases`
  (seeded global reference cases), and the operational diagnostics endpoints
  (`/readiness`, `/storage/health`, etc., which use `get_current_user` where
  they expose environment detail).

## Guard-level convention applied

- Read-only project data uses `require_project_read`.
- Routes that generate, create, promote, regenerate, or mutate reviewer state
  use `require_project_reviewer`.
- Routes keyed by a raw entity id (document, chunk, plan sheet, CAD file, parse
  run, CAD finding, workflow item, review packet, plan consistency finding,
  checklist item, finding, AI run, draft finding, evaluation result, response
  package, review cycle, resubmittal, applicant response, comparison run,
  resolution record) resolve the owning project first, then apply the guard, so
  a raw id cannot bypass tenant scoping. Mutating raw-id routes enforce the
  guard when the entity resolves and otherwise let the service raise its
  existing 404.

## Risks found and their current status

1. Raw-entity-id bypass. CLOSED across the API. Every raw-id route now resolves
   the owning project and guards on it (`GET /documents/{document_id}`,
   `GET /plan-sheets/{sheet_id}`, `GET /cad-metadata/{cad_metadata_id}`,
   `GET /chunks/{chunk_id}`, `GET /review-packets/{packet_id}`,
   `GET /workflow-items/{id}`, `GET /review-cycles/{id}`,
   `GET /resubmittals/{id}`, `GET /revision-comparisons/{id}`, and the rest).
2. Unguarded project-scoped read routes. CLOSED. All previously unguarded
   routers now call a guard.
3. Child entities have no independent tenancy column, so correctness still
   depends on the guard being applied at every route. This is now true for every
   project-owned route; the residual risk is a future route shipping without a
   guard (see deferred work for the recommended automated check).
4. Demo-mode posture. With `AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS=false` and
   `AUTH_DEMO_MODE=true` (the prototype default), anonymous callers fall back to
   a demo reviewer identity on real projects. This is acceptable for a prototype
   but must be off in production multi-tenant operation. Unchanged in this phase.

## Hardening completed

Phase 2A:

- `traceability.py`: `require_project_read` on the GETs and
  `require_project_reviewer` on the review-action POST.
- `documents.py`: `GET /documents/{document_id}` resolves the document's project
  and calls `require_project_read`.

Phase 2B (this pass): added the guards above to every remaining project-owned
router and closed every raw-id bypass. Public Brookside Meadows demo reads stay
anonymous through both project-scoped and raw-id routes. No analytical behavior
changed; the edits add access checks and project resolution only.

## Tests added

In `backend/tests/test_tenant_isolation.py`:

- Phase 2A: traceability (member 200, non-member 403, review-action 403,
  anonymous-strict 401, demo public 200) and document raw-id (non-member 403,
  owner 200).
- Phase 2B: a parametrized matrix over 29 project-scoped read paths spanning
  every hardened router (CAD intake, CAD metadata, workflow board, review
  packets, plan consistency, plan references, plan sheets, sheet hotspots,
  hotspots, checklist, chunks, AI review, human review, evaluation, review
  cycles, resubmittals, applicant responses, carry-forwards, resolution records,
  response packages, audit events, traceability, command center) asserting
  non-member 403, owner 200, and anonymous demo 200. Plus a raw-id cross-tenant
  test (review cycle: non-member 403, owner 200), an anonymous-under-strict-login
  block (401), and a plan-sheet raw-id demo-public check.

The pilot request suite (`backend/tests/test_pilot_requests.py`) also asserts the
public/protected boundary for the lead endpoint: anyone may submit, only an
authenticated user may list.

## Public demo behavior

Preserved. The Brookside Meadows demo project (`proj_brookside_meadows`,
`demo_public = True`) remains readable without a login through both
project-scoped and raw-id routes, so `/guided-demo`, the homepage, and the demo
surfaces keep working. The frontend `safeFetch` helper returns `null` on a 401 or
403 and callers fall back to seeded data, so guarded responses never surface a
stack trace.

## Release readiness

The project-owned API surface now uniformly enforces tenant access, and raw-id
bypasses are closed, which removes the cross-tenant data-leak class that would
block a B2B deal. This is the access-control prerequisite for the next phase. It
is not, by itself, production multi-tenancy: the prototype still defaults to the
anonymous demo-reviewer fallback for real projects, runs on SQLite, and has no
full auth lifecycle or billing. Those remain deferred.

## Deferred work before production SaaS

- Add an automated check (a test that introspects the router table) that every
  project-scoped route references a guard, so a new route cannot ship without
  one.
- Turn off the anonymous demo-reviewer fallback for real projects in production
  and require a signed-in member (`AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS=true`,
  `AUTH_DEMO_MODE=false`).
- Consider denormalizing `organization_id` onto child entities, or enforcing a
  single query helper that always joins through the project, to remove the
  per-route dependency.
- The broader Phase 2 items (Postgres, full auth lifecycle, billing, live AI)
  remain out of scope for this phase and are tracked in the SaaS roadmap.
