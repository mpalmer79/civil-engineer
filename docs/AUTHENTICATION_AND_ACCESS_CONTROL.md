# Authentication and Access Control

This document describes the local authentication and access-control foundation
added in Production Foundations Sprint 5.

It is a local auth foundation, not enterprise single sign-on. It protects review
records and improves audit attribution. It never approves plans, certifies
compliance, validates design, or makes any final engineering decision.

## Local auth approach

Authentication is local: a user registers with an email, display name, and
password, then signs in to receive a short-lived access token. The backend (FastAPI)
verifies every protected request against the token. There is no third-party
identity provider in this sprint.

## Password hashing approach

Passwords are hashed with PBKDF2-HMAC-SHA256 from the Python standard library,
using a per-user random salt and a fixed iteration count. The stored value is
`pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`. Verification uses a
constant-time comparison. Plaintext passwords are never stored, never logged, and
never placed in audit metadata. Password hashes are never returned by the API.
A standard-library approach avoids fragile native build dependencies; a
production system may swap in a memory-hard hash (for example Argon2) behind the
same `hash_password`/`verify_password` interface.

## Token and session approach

Access tokens are HMAC-SHA256 signed (the HS256 construction a JWT uses) over a
small JSON payload carrying the user id, email, issued-at, and expiry. They are
signed with `AUTH_SECRET_KEY` and expire after `AUTH_TOKEN_EXPIRE_MINUTES`
(default 120). The signature and expiry are validated on every request using a
constant-time comparison. Tokens are stateless, so sign-out is handled
client-side by discarding the token. Tokens are never logged, never placed in
URLs, and never stored in audit metadata. A production system should move toward
hardened session handling, rotation, or SSO.

## Organization accounts

An `Organization` groups users and projects. Organization types include
municipality, consulting_engineer, developer_applicant, county_agency,
demo_organization, and internal_demo. A user joins an organization through an
`OrganizationMembership` that carries a role.

## Role definitions

Membership roles: org_admin (manages organization users and project access),
senior_reviewer and reviewer (reviewer actions), read_only (view only),
applicant_placeholder (limited, no reviewer actions yet), and demo_reviewer
(behaves as a reviewer for the local demo).

## Project access model

`ProjectAccess` grants a user or an organization an access level on a project:
project_admin, senior_reviewer, reviewer, read_only, or applicant_placeholder.
The effective access level for a user is the strongest of their direct grants,
their organization's grants, and an implicit project_admin when they are an
org_admin of the project's organization. Creating a project grants the creator
project_admin access.

## Route protection

- Read routes (project detail, documents, findings, and the like) require read
  access. A `demo_public` project is readable without a login when
  `AUTH_ALLOW_PUBLIC_DEMO` is true.
- Reviewer-action routes (create document, upload, index PDF, create finding,
  create citation, search and save evidence candidates, promote candidates,
  update checklist items, create checklists, create draft findings) require
  reviewer access.
- Access-management routes (grant project access, manage membership) require
  project_admin or org_admin.
- Unauthenticated protected requests return 401; authenticated requests without
  permission return 403.

## Frontend guarded states

The frontend stores the access token client-side and attaches it as a Bearer
Authorization header. Signed-out users see a sign-in prompt for real project
records and a clear path to the public demo. A `PermissionDeniedCard` shows calm,
review-support messaging when access is missing. Server components run
unauthenticated and therefore show public demo data; authenticated views fetch
client-side. Production should move toward hardened session handling or SSO.

## Demo-mode behavior

The seeded Brookside Meadows project is `demo_public` and remains readable
without a login. The seeded demo organization, demo reviewer
(reviewer@example.com), and demo admin (admin@example.com) exist for local
development and the portfolio demo only; their passwords are local demo values
and must be changed or disabled before any real use. When
`AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS` is false, unauthenticated reviewer actions
fall back to the demo reviewer so the self-contained demo and the existing
seeded workflow keep working.

## Audit attribution

When a signed-in user takes an action, the audit event records the user id, user
email, organization id, and access level. Audit metadata never includes
passwords, password hashes, tokens, secrets, API keys, raw server file paths, or
full extracted page text.

## Limitations

- Local authentication only; no SSO yet.
- No hardened production session system yet (stateless tokens, client-side
  storage).
- No full applicant portal yet; the applicant role is a limited placeholder.
- No enterprise tenant isolation claims.
- The demo reviewer and public demo behavior remain available by configuration.
- Uploaded files remain local unless deployment storage is configured.

## Future SSO and tenant isolation work

Later sprints may add SSO (SAML, Microsoft Entra, Google Workspace), hardened
session handling, full applicant portal workflows, and enterprise tenant
isolation. Each must keep the professional boundary: access control governs who
can review records, not whether a project satisfies engineering requirements, and
a licensed Professional Engineer remains responsible for engineering decisions.
