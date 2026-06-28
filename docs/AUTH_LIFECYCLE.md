# Authentication and Account Lifecycle

What account lifecycle and team access Civil Engineer AI implements today, added
in Production Phase 4B. It builds on the local authentication foundation
(`docs/AUTHENTICATION_AND_ACCESS_CONTROL.md`) and the Postgres/migration
foundation (`docs/PRODUCTION_DATABASE.md`). It pairs with
`docs/BILLING_AND_USAGE.md`.

Access control protects review records and improves audit attribution. It never
grants engineering authority and never implies approval, certification, or
compliance. A human reviewer remains responsible for every finding.

## What is implemented

- Sign up, sign in, sign out, and the current-user check (from the prior phase).
- An aggregate account profile (`GET /api/v1/account/profile`) returning the
  signed-in user and a summary of their organization memberships.
- Password reset by token, with hashed token storage, expiry, and use-once.
- Organization team invitations: invite by email with a role, list, revoke, and
  accept. Invitation tokens are hashed, expire, and cannot be reused.
- Role-aware organization access for team management.

## What is not implemented

- Email confirmation at sign-up is deferred. It is not required for the local
  account model and adds friction without an email provider; it can be added
  behind the same mailer interface in a future phase.
- Single sign-on (SSO) and enterprise directory sync are out of scope.
- No real email is sent. See the Email section below.

## Password reset

Endpoints (`backend/app/api/v1/auth.py`):

- `POST /api/v1/auth/password-reset/request` with `{ "email": "..." }`. The
  response is uniform whether or not an account exists, so the endpoint never
  reveals which emails are registered. When the email matches an active account,
  a reset token is created and delivered through the mailer.
- `POST /api/v1/auth/password-reset/confirm` with `{ "token": "...",
  "new_password": "..." }`. Sets the new password when the token is valid,
  unused, and unexpired, then marks the token used.

Security properties:

- Tokens are stored only as a one-way SHA-256 hash
  (`password_reset_tokens.token_hash`). The plaintext token is never persisted.
- Tokens expire after `AUTH_PASSWORD_RESET_EXPIRE_MINUTES` (default 60).
- A token works once; on use it is marked used, and requesting a new token
  invalidates older unused tokens for that account.
- The reset token is never logged.

Token delivery:

- In production, the token is delivered by email. No email provider is wired in
  this phase (see Email), so a production deployment must configure one before
  onboarding real users.
- Outside production, when `AUTH_EXPOSE_DEV_TOKENS` is on, the request response
  also returns the plaintext token (`dev_reset_token`) so local development and
  tests can complete the flow without an email provider. This is forced off in
  production regardless of the flag.

Frontend: `/reset-password` (request) and `/reset-password/confirm` (set a new
password). The login form links to the reset page.

## Organization team invitations

Endpoints (`backend/app/api/v1/invitations.py`):

- `POST /api/v1/organizations/{organization_id}/invitations` (org_admin) with
  `{ "email": "...", "role": "reviewer" }`. Creates a pending invitation.
- `GET /api/v1/organizations/{organization_id}/invitations` (org_admin). Lists
  invitations with their current status.
- `POST /api/v1/organizations/{organization_id}/invitations/{invitation_id}/revoke`
  (org_admin). Revokes a pending invitation.
- `GET /api/v1/invitations/lookup?token=...` (public). Returns a safe preview
  (organization, email, role, status) for the accept page. The token is not
  echoed back.
- `POST /api/v1/invitations/accept` (signed-in user) with `{ "token": "..." }`.
  Creates an active membership in the organization with the invited role.

Invitable roles: `org_admin`, `senior_reviewer`, `reviewer`, `read_only`. The
internal `demo_reviewer` and `applicant_placeholder` roles are not invitable.

Security properties:

- Invitation tokens are stored only as a one-way hash
  (`organization_invitations.token_hash`); the plaintext token is never
  persisted.
- Invitations expire after `AUTH_INVITATION_EXPIRE_DAYS` (default 14). Expired,
  accepted, and revoked invitations cannot be accepted.
- Only an org_admin of the organization can invite, list, or revoke. A
  non-admin member and an anonymous caller are rejected (403/401).
- Outside production, the create response includes `dev_invite_token` so the
  accept flow can be completed locally; it is null in production.

Frontend: `/workspace/team` (admins invite, list, and revoke; members see the
member list) and `/invitations/accept` (preview and accept; signed-out visitors
are prompted to sign in or register first).

## Roles and operator access

Roles are unchanged from the prior phase and are reused as-is:

- Organization membership roles: `org_admin`, `senior_reviewer`, `reviewer`,
  `read_only` (plus internal `demo_reviewer` and `applicant_placeholder`).
- Per-project access levels: `project_admin`, `senior_reviewer`, `reviewer`,
  `read_only`.

Operator access (the pilot admin) remains gated to an organization admin
(`org_admin`). A dedicated `pilot_operator` role was considered and deliberately
not added: org_admin is sufficient and avoids broad membership-model churn. See
`docs/PILOT_OPERATIONS.md` for the operator model.

Two organization-scoped guards back team management
(`backend/app/services/access_control_service.py`): `require_org_member` (any
active member) and `require_org_admin` (org_admin of that organization).

## Email

No real email is sent in this phase. A mailer abstraction
(`backend/app/services/mailer.py`) provides a default `noop` provider that
records a safe, redacted delivery log and sends nothing. It never logs a reset
token, an invitation token, a password, or any secret.

Before onboarding real users, a production deployment must wire a real email
provider behind this interface and turn off `AUTH_EXPOSE_DEV_TOKENS` (it is
forced off in production regardless).

## Environment variables

Backend service variables (set on the backend only):

- `AUTH_PASSWORD_RESET_EXPIRE_MINUTES` (default 60).
- `AUTH_INVITATION_EXPIRE_DAYS` (default 14).
- `AUTH_EXPOSE_DEV_TOKENS` (default true; forced off in production) controls
  whether reset/invite tokens are returned in API responses for local use.
- `EMAIL_PROVIDER` (default `noop`) and `EMAIL_FROM`.

## Migrations

The schema for password reset tokens and organization invitations is created by
the Alembic migration `0002_auth_billing_usage`. Apply it with `alembic upgrade
head`. See `docs/PRODUCTION_DATABASE.md`.

## Tests

Backend: `backend/tests/test_auth_lifecycle.py` covers password reset
request/confirm, expiry, use-once, hashed storage, the account profile, and the
full invitation workflow (create, list, revoke, accept, role enforcement,
non-admin rejection, reuse protection, and the public lookup). Frontend:
`app/__tests__/accountBillingTeam.test.tsx` covers the reset forms, the team
client, and the accept-invite client.

## Remaining work before production onboarding

- Wire a real email provider and disable dev token exposure.
- Add email confirmation at sign-up if required by the onboarding flow.
- Consider SSO for larger customers (out of scope here).
