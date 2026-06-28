# Release Readiness

An honest snapshot of what Civil Engineer AI is ready for: an early
design-partner pilot, not production multi-tenant SaaS. It pairs with
`docs/PILOT_RELEASE_CHECKLIST.md` (the step-by-step verification) and
`docs/TENANT_ISOLATION_AUDIT.md` (the access-control detail).

## Public demo status

The Brookside Meadows sample project (`proj_brookside_meadows`) is a seeded
review-support demo. It is `demo_public`, so it stays readable without a login
through both project-scoped and raw-id routes. The homepage, `/guided-demo`,
`/start-here`, and the Brookside surfaces (CAD intake, plan consistency,
traceability, workflow board, review packets, command center) all run on this
seeded data plus CAD findings produced by really parsing a bundled sample DXF.

## Guided demo flow

`/guided-demo` is a public, no-login product tour over Brookside Meadows. It opens
with fixture-backed proof counts (degrading to qualitative cards when the backend
is unavailable), walks five AEC pre-submittal QA steps, and ends with a pilot CTA
to `/pilot`. The boundary statement is present below the tour, not in the lead.

## Pilot request flow

`/pilot` is a public design-partner request form (name, work email, firm, role,
project type, primary pain, interest level, optional notes, and a sample-package
checkbox). It collects no file uploads. Submissions persist via
`POST /api/v1/pilot-requests`, show an honest success state, and never claim an
email was sent (none is configured). On failure the form shows an error and stays
put; it never fakes success.

## Pilot operator/admin workflow

A signed-in organization admin can review submitted requests at
`/admin/pilot-requests`, backed by the admin-gated `GET /api/v1/pilot-requests`.
Anonymous visitors get an unauthorized state, and a signed-in non-admin gets a
forbidden state; neither sees any data. There is no public list endpoint and no
file-upload control. Finer-grained, dedicated pilot-operator roles are future
work; organization admin is the current operator gate.

`/workspace` is the signed-in operator home: identity, organization, accessible
project counts, the pilot/release state, and quick links into projects, the
guided demo, the public pilot form, and (for operators) pilot requests.
`/workspace/settings` is an explicit placeholder; every section is marked
"coming later" and nothing there is active.

## Tenant guard status

Every project-owned API route enforces the project access guards
(`require_project_read` / `require_project_reviewer` / `require_project_admin`),
and all raw-id routes resolve the owning project before guarding. A
guard-regression test (`backend/tests/test_guard_coverage.py`) fails if a new
`{project_id}` route ships without a guard. The Brookside demo exception is scoped
to that one project. See `docs/TENANT_ISOLATION_AUDIT.md`.

## Production-posture environment profile

For a public pilot deployment, set these backend flags so real project data is
protected while the public demo keeps working:

- `AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS=true` - a real project rejects anonymous
  access (401) and non-member access (403).
- `AUTH_DEMO_MODE=false` - turns off the anonymous demo-reviewer fallback for real
  projects.
- `AUTH_ALLOW_PUBLIC_DEMO=true` - keeps the Brookside demo project readable
  without a login.

For a production SaaS deployment, also set `APP_ENV=production` and point
`DATABASE_URL` at a Postgres database, then run `alembic upgrade head`. In
production mode the backend refuses to start on SQLite. SQLite stays the default
for local development and the pilot prototype. See `docs/PRODUCTION_DATABASE.md`.

`backend/tests/test_release_posture.py` pins this behavior: under these flags the
Brookside demo stays anonymously readable, a real project rejects anonymous (401)
and non-member (403) access, the owner reads it (200), public pilot submission
still works, and the pilot admin list stays protected (401 for anonymous).

## Public route allowlist

Only these surfaces are intended to be reachable without a login:

- `/` (homepage)
- `/guided-demo`
- `/pilot`
- `/start-here`
- The Brookside Meadows demo project surfaces used by the guided demo
  (`/projects/proj_brookside_meadows/...`), which stay public because the project
  is `demo_public`.
- `/health` and `/api/v1/readiness` (no secrets in their output).
- Static assets under `public/`.

Everything else is protected: `/workspace`, `/workspace/settings`,
`/admin/pilot-requests`, all real tenant projects and their project-owned API
routes, and the pilot request list/admin/export/status/notes APIs. This allowlist
is enforced by the access guards and the auth posture flags above, not by a
separate route table, so a new project-owned route is protected by default and is
caught by the guard-regression test if it is not.

## Pilot operations

Submitted pilot requests carry an operator pipeline status (`new`, `contacted`,
`qualified`, `active_pilot`, `closed`, `rejected`), operator-only internal notes,
and a last-contacted timestamp. An organization admin can filter, search, update
status, save notes, and export a CSV at `/admin/pilot-requests`. Internal notes
are never returned by the public submission endpoint. See
`docs/PILOT_OPERATIONS.md` and `docs/DESIGN_PARTNER_OUTREACH.md`.

## Production database foundation

The data layer is now production-ready in posture. SQLite remains the default for
local development and tests, and Postgres is required for production SaaS. The
provider is selected from `DATABASE_URL`, the legacy `postgres://` scheme is
normalized automatically, and the schema is managed with Alembic migrations
(initial migration `0001_initial_schema`, which includes the pilot request
operator fields). In strict production mode (`APP_ENV=production`) the backend
refuses to start on SQLite. The public readiness summary reports the deployment
mode, the database provider class, and the migration control state without
exposing any secret. See `docs/PRODUCTION_DATABASE.md` for the full migration
path, commands, and Railway/Postgres setup.

## Account lifecycle, team, and billing foundation

The production SaaS account foundation now exists. Password reset (hashed,
expiring, use-once tokens) and organization team invitations (invite by email
with a role, list, revoke, accept) are implemented, with org_admin gating for
team management. A billing-readiness foundation is in place: code-defined plans
(`demo`, `design_partner`, `professional`, `team`), per-organization
subscriptions, advisory usage metering, and workspace billing/usage/team pages.
Stripe is deferred and billing is honestly inactive: no payment is collected and
no subscription is charged. No real email is sent; a no-op mailer abstraction
stands in until a provider is wired. See `docs/AUTH_LIFECYCLE.md` and
`docs/BILLING_AND_USAGE.md`.

## Current limitations

- Database: SQLite for local development and tests; Postgres required for
  production SaaS. Alembic migrations are in place. Postgres handling is verified
  at the URL/configuration level in the suite; manual Postgres verification is
  documented in `docs/PRODUCTION_DATABASE.md`.
- Auth: local accounts and bearer tokens. Password reset and team invitations
  are implemented; email confirmation and SSO are not. No real email is sent yet.
  The prototype default still allows an anonymous demo-reviewer fallback for real
  projects; production must turn that off.
- Billing: not active. The plan and usage foundation exists, but Stripe checkout
  and webhooks are deferred and no payment is collected.
- Live AI: disabled by default. The default provider is a deterministic mock;
  live calls require an explicit provider, an enable flag, and a key.
- Capability scope: real DXF parsing (ezdxf) and PDF text-layer indexing (pypdf)
  only. No OCR, DWG, GIS, computer vision, or vector search. See
  `docs/SAAS_POSITIONING.md` for the canonical capability wording.

## What is ready for design-partner conversations

- A media-forward homepage and a public, no-login guided demo.
- A working public pilot request flow with persisted leads.
- A protected operator view to triage those leads.
- A signed-in workspace home and a release-ready project list.
- Uniform tenant access control with a guard-regression test.
- A documented health check and a public readiness summary.

## What is not ready for production customers

- The production database foundation (Postgres support and Alembic migrations)
  and the account-lifecycle foundation (password reset, team invitations) are in
  place, but billing is not active and no email provider is wired.
- Self-serve paid onboarding is not active: Stripe checkout and webhooks are
  deferred, and email confirmation and SSO are not implemented.
- Live AI is intentionally off by default.
- The anonymous demo-reviewer fallback must be disabled before real tenant data
  is hosted.

## Release recommendation

Ready for a design-partner pilot: share the public site and guided demo, collect
pilot requests, and run scoped conversations. Not ready to host real, paying,
multi-tenant customer data until the production-posture items above are
addressed. Treat this as a pilot-ready prototype.
