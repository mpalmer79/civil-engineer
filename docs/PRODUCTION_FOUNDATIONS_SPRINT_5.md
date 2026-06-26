# Production Foundations Sprint 5: Real Authentication, Reviewer Roles, and Project Access Control

This sprint adds the first real authentication and access-control foundation.
Real users can sign in, belong to organizations, hold reviewer or admin roles,
and access only the projects they are permitted to view or act on, with real
audit attribution.

The product moves from "actions are attributed to a demo reviewer identity" to
"real users can sign in, belong to organizations, hold reviewer/admin/applicant
style roles, and access only the projects they are permitted to view or act on."

This is a local authentication foundation, not enterprise single sign-on.
Authentication and roles protect review records and improve audit attribution.
They never introduce final engineering decision workflows. Civil Engineer AI
still does not approve plans, certify compliance, verify CAD, validate design,
declare a project safe, or replace a licensed Professional Engineer.

Live demo: https://civil-engineer.up.railway.app/

## What Sprint 5 adds

Backend:

- `UserAccount`, `Organization`, `OrganizationMembership`, and `ProjectAccess`
  models, plus Sprint 5 fields on `Project` (`organization_id`,
  `created_by_user_id`, `visibility_mode`, `demo_public`) and on `AuditEvent`
  (`user_id`, `user_email`, `organization_id`, `access_level`).
- `auth_service`: PBKDF2-HMAC-SHA256 password hashing and HMAC-SHA256 signed
  access tokens (the HS256 construction a JWT uses), both from the Python
  standard library, so there is no fragile native dependency.
- `access_control_service`: resolves the signed-in user from a bearer token,
  decides read, reviewer, and admin access per project, records access grants,
  and seeds the demo organization, demo users, and demo access.
- Auth, organization, current-user, and project-access API routes.
- Route protection on real-project read and reviewer-action routes, with public
  demo and demo reviewer fallback preserved.
- Authenticated audit attribution threaded into project, document, finding, and
  checklist actions.

Frontend:

- `lib/api/auth.ts` client and a central token wrapper that attaches the
  Authorization header and handles 401/403 cleanly.
- Login, register, account, organizations, organization detail, and project
  access pages, plus a `PermissionDeniedCard`, an `AccountNav` sign-in/out
  control, and a `SignInNotice`.
- Navigation and projects pages updated for signed-in and signed-out states.
- A homepage update describing Sprint 5.

## How this builds on Sprints 1 through 4

Sprints 1 through 4 created real projects, documents, findings, citations,
evidence retrieval, candidate queues, and checklist-driven review, all attributed
to a single demo reviewer identity. Sprint 5 replaces that placeholder with real
user accounts and access control: project creation now records the creating user
and organization and grants them project_admin access; reviewer-action routes
require reviewer access; and audit events carry the user and organization
identity. The seeded Brookside Meadows demo remains a public demo so every prior
sprint's demo behavior is preserved.

## Why authentication comes before applicant portal, SSO, and enterprise integrations

Identity and access control are the substrate every later access feature depends
on. An applicant portal needs a limited applicant role; SSO needs a user and
organization model to map identities into; tenant isolation needs organizations
and project access to enforce. Building a clean local user, organization, role,
and project-access model first means those later features extend a known
foundation instead of reworking attribution and authorization.

## What remains demo-only

Brookside Meadows is a public demo (`demo_public`) and stays readable without a
login when `AUTH_ALLOW_PUBLIC_DEMO` is true. The seeded demo organization, demo
reviewer (reviewer@example.com), and demo admin (admin@example.com) exist for
local development and the portfolio demo only. Their passwords are local demo
values and must be changed or disabled before any real use. When
`AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS` is false (the default in the test suite
and the self-contained demo), unauthenticated reviewer actions fall back to the
demo reviewer so the existing seeded workflow keeps working.

## What remains out of scope

SAML and enterprise SSO, Microsoft Entra and Google Workspace SSO, billing and
payments, full applicant portal workflows, external email dependencies, live AI
calls, OCR, DWG parsing, GIS, Bluebeam, automated engineering calculations,
geometry or design validation, and final approval workflows are out of scope.
This sprint is a local authentication and access-control foundation only.

## How organizations, users, roles, and project access work

- A `UserAccount` is a real local user with a hashed password.
- An `Organization` groups users; an `OrganizationMembership` gives a user a role
  in an organization (org_admin, senior_reviewer, reviewer, read_only,
  applicant_placeholder, demo_reviewer).
- `ProjectAccess` grants a user or organization an access level on a project
  (project_admin, senior_reviewer, reviewer, read_only, applicant_placeholder).
- Read access is required to view a project's records; reviewer access is
  required to take reviewer actions; project_admin or org_admin is required to
  manage project access.
- A `demo_public` project (the seeded demo) may be read without a login when
  configured. Real projects are `controlled` and require explicit access.

## How real audit attribution replaces demo reviewer attribution

When a signed-in user takes an action, the audit event records the user id, user
email, organization id, and access level alongside the existing actor display
name, instead of the shared demo reviewer. Audit metadata never includes tokens,
passwords, password hashes, secrets, raw server file paths, or full extracted
page text.

## How to test the workflow locally

Backend:

```
cd backend
pip install -r requirements.txt pytest-cov
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

The auth tests live in `tests/test_auth_access_control.py`.

Frontend:

```
npm install
npm run typecheck
npm run lint
npm test
npm run build
```

Manual end-to-end: open the app, register an account (optionally creating an
organization), create a project (you become its project_admin), and take reviewer
actions. Open another account and confirm it cannot read or act on your project.
Confirm the public Brookside Meadows demo remains readable without a login.

## Security summary

- Passwords are hashed (PBKDF2-HMAC-SHA256, per-user salt); plaintext is never
  stored and hashes are never returned by the API.
- Access tokens are signed with `AUTH_SECRET_KEY`, short-lived, never logged, and
  never placed in URLs or audit metadata.
- Unauthenticated protected requests return 401; authenticated requests without
  permission return 403, with calm review-support messaging.

See [AUTHENTICATION_AND_ACCESS_CONTROL.md](AUTHENTICATION_AND_ACCESS_CONTROL.md)
for the design and [API_AUTH_AND_ACCESS_CONTROL.md](API_AUTH_AND_ACCESS_CONTROL.md)
for the API contract. The recommended next sprint is Production Foundations
Sprint 6: Durable Object Storage and Deployment-Ready File Persistence.
