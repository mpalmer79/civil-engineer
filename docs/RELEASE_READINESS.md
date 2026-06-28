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

## Current limitations

- Database: SQLite. No Postgres migration in this phase.
- Auth: local accounts and bearer tokens only. No password reset, no team
  invitations, no SSO. The prototype default still allows an anonymous
  demo-reviewer fallback for real projects; production must turn that off.
- Billing: not active. No Stripe, no payment, no plans.
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

- No production database, auth lifecycle, or billing.
- No team invitations or self-serve onboarding.
- Live AI is intentionally off by default.
- The anonymous demo-reviewer fallback must be disabled before real tenant data
  is hosted.

## Release recommendation

Ready for a design-partner pilot: share the public site and guided demo, collect
pilot requests, and run scoped conversations. Not ready to host real, paying,
multi-tenant customer data until the production-posture items above are
addressed. Treat this as a pilot-ready prototype.
