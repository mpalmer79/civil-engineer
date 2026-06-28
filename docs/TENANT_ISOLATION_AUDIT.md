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

Verified by inspecting each router for guard usage.

Enforced (call `require_project_*` or `get_current_user`):

- `projects.py`, `documents.py`, `findings.py`, `evidence_retrieval.py`,
  `dashboard.py`, `checklist_review.py`, `auth.py`, and `traceability.py`
  (hardened in this pass).

Not yet enforcing project access (no guard reference found):

- `cad_intake.py`, `cad_metadata.py`, `workflow.py`, `review_packets.py`,
  `plan_consistency.py`, `command_center.py`, `plan_sheets.py`, and several
  raw-entity-id lookups (for example `plan_sheets.py` and `cad_metadata.py`
  fetch by sheet or metadata id with no project context).

## Risks found

1. Raw-entity-id bypass. Read endpoints keyed by a raw child-entity id without a
   project context can return data across tenants. Confirmed and fixed for
   `GET /documents/{document_id}`. The same shape still exists for
   `GET /plan-sheets/{sheet_id}`, `GET /cad-metadata/{cad_metadata_id}`, and
   similar lookups.
2. Unguarded project-scoped read routes. The routers listed above read
   project-scoped data without calling a guard, so any caller who knows a
   `project_id` can read another tenant's CAD, workflow, plan-consistency,
   command-center, review-packet, and plan-sheet data.
3. Child entities have no independent tenancy column, so correctness depends on
   the guard being applied at every route. A single missing guard is a leak.
4. Demo-mode posture. With `AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS=false` and
   `AUTH_DEMO_MODE=true` (the prototype default), anonymous callers fall back to
   a demo reviewer identity on real projects. This is acceptable for a prototype
   but must be off in production multi-tenant operation.

## Hardening completed in this pass

- `traceability.py`: added `require_project_read` to the project traceability GET
  and the review-action history GET, and `require_project_reviewer` to the
  review-action POST. Public demo reads still work; non-members of a real project
  now receive 403, and anonymous callers receive 401 when login is required.
- `documents.py`: `GET /documents/{document_id}` now resolves the document's
  project and calls `require_project_read`, closing the raw-id bypass for
  documents.

## Tests added

In `backend/tests/test_tenant_isolation.py`:

- A non-member cannot read another project's traceability (403).
- The owner can read their own project's traceability (200).
- A non-member cannot record a traceability review action (403).
- An anonymous caller cannot read a real project's traceability under strict
  login (401).
- The public demo project's traceability stays readable anonymously, including
  under strict login (200).
- A non-member cannot fetch a document by raw id (403); the owner can (200).

The pilot request suite (`backend/tests/test_pilot_requests.py`) also asserts the
public/protected boundary for the new lead endpoint: anyone may submit, only an
authenticated user may list.

## Deferred work before production SaaS

- Apply `require_project_*` to the remaining unguarded routers
  (`cad_intake`, `cad_metadata`, `workflow`, `review_packets`,
  `plan_consistency`, `command_center`, `plan_sheets`) and to raw-id lookups for
  plan sheets and CAD metadata, with cross-tenant tests for each, ideally by
  centralizing the project-resolution-plus-guard step.
- Add an automated check that every project-scoped route references a guard, so a
  new route cannot ship without one.
- Turn off the anonymous demo-reviewer fallback for real projects in production
  and require a signed-in member.
- Consider denormalizing `organization_id` onto child entities, or enforcing a
  single query helper that always joins through the project, to remove the
  per-route dependency.
- The broader Phase 2 items (Postgres, full auth lifecycle, billing, live AI)
  remain out of scope for this phase and are tracked in the SaaS roadmap.
