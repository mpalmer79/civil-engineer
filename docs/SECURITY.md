# Security and Professional Boundary

This is the canonical security reference for Civil Engineer AI. It covers the
professional and liability boundary, the backend-for-frontend proxy threat model,
authentication and access control, the account lifecycle, tenant isolation, the
comment-letter template boundary, and known limitations. It folds in the former
security-and-professional-boundary, authentication-and-access-control,
auth-lifecycle, tenant-isolation-audit, and comment-letter-template-boundary
documents, and it summarizes the detailed threat model kept at
`docs/security/BFF_PROXY_THREAT_MODEL.md`.

## Professional and liability boundary

Civil Engineer AI is review-support only. It helps a human reviewer organize
evidence, draft review-support findings, track workflow, and prepare
reviewer-controlled response language.

It does not approve plans, certify compliance, stamp drawings, verify CAD,
validate design, declare a project safe, make final engineering decisions, close
or resolve issues, or replace a licensed Professional Engineer. There is no
action named approve. A licensed Professional Engineer remains responsible for
every final decision, and every review-support output exists to inform that human
decision, never to substitute for it.

Enforcement:

- Project, document, finding, and evidence statuses are constrained to a
  review-support vocabulary in the `app/core/vocab` package and `app/core/safety`.
- User-provided text for projects, documents, and findings is rejected if it
  contains final-decision wording (for example approved, certified, fully
  compliant, safe).
- Comment-letter drafts are generated from fixed deterministic templates with a
  fixed review-support boundary statement rendered on every draft and preview,
  which is never an editable section. There are no live AI calls in that path.
- A repository-wide content gate (`scripts/check-content-integrity.mjs`) blocks
  prohibited wording and attribution text in CI.

## Authentication and sessions

- Passwords are hashed with PBKDF2-HMAC-SHA256 and a per-user salt. Plaintext
  passwords are never stored, never logged, and never placed in audit metadata.
  Password hashes are never returned by the API.
- Access tokens are HMAC-SHA256 signed with `AUTH_SECRET_KEY`, short-lived, never
  logged, never placed in URLs, and never stored in audit metadata.
- The browser never holds the token. Sign-in stores it in an HttpOnly cookie
  whose lifetime comes from the backend's stated token expiry, and a same-origin
  proxy attaches it server-side. Session truth comes from a validated status
  endpoint, and an invalid session clears its cookies.

### Account lifecycle

- Password reset by token: `POST /api/v1/auth/password-reset/request` and
  `/confirm`. The request response is uniform whether or not an account exists.
  Reset tokens are stored only as a one-way SHA-256 hash, expire after
  `AUTH_PASSWORD_RESET_EXPIRE_MINUTES`, and are use-once. The reset token is never
  logged.
- Organization team invitation: invite by email with a role, list, revoke, and
  accept. Invitation tokens are hashed, expire after `AUTH_INVITATION_EXPIRE_DAYS`,
  and cannot be reused once accepted, revoked, or expired. Only an org_admin can
  invite, list, or revoke.
- Email confirmation at sign-up and single sign-on are deferred and out of scope.
- Token delivery goes through the mailer abstraction. The default `noop` provider
  sends nothing; the `smtp` provider delivers real reset and invitation email when
  configured. Outside production, dev tokens are returned in API responses for
  local flows; this is forced off in production. See `docs/OPERATIONS.md` for the
  email configuration.

## Backend-for-frontend proxy threat model

All authenticated browser requests go through a same-origin proxy that forwards
only validated backend API paths to the configured FastAPI origin. The detailed
threat model is kept at `docs/security/BFF_PROXY_THREAT_MODEL.md`; the enforced
controls are:

- Route-class request body limits and upstream timeouts, with uploads streamed
  rather than buffered.
- An allowlist of request and response headers.
- The access token is attached server-side from the HttpOnly cookie; invalid
  sessions are cleared on a 401.
- Every request is stamped with a correlation ID.
- CSRF protection: every cookie-authenticated mutating request must pass two
  independent checks. When an Origin header is present it must match the trusted
  application origin exactly, and the request must carry a custom header that a
  cross-site attacker cannot set without a CORS preflight the browser refuses.
  Cross-origin mutations receive an explicit 403.

## Tenant isolation and access control

Organizations, memberships, roles, and per-project access grants gate every
project-owned API route. The canonical guards are `require_project_read`,
`require_project_reviewer`, and `require_project_admin`, backed by
`backend/app/services/access_control_service.py`. Unauthenticated protected
requests return 401; authenticated requests without permission return 403 with no
data and no fixture substitution.

- Child entities reference `project_id` only, so their isolation depends on the
  guard being applied at every route. Every `{project_id}` route and every raw-id
  route (resolving the owning project first) now applies a guard.
- A guard-regression test (`backend/tests/test_guard_coverage.py`) fails if a new
  `{project_id}` route ships without a guard, so a new project-owned route is
  protected by default.
- The Brookside Meadows project (`proj_brookside_meadows`) is marked `demo_public`
  and stays anonymously readable when `AUTH_ALLOW_PUBLIC_DEMO` is set. This
  exception is intentional and scoped to the demo project; it is not a model for
  tenant-owned customer data.

This is an honest snapshot of what is enforced today.
It does not claim production-grade tenant isolation. The prototype still defaults
to an anonymous
demo-reviewer fallback for real projects, which must be turned off in production
(`AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS=true`, `AUTH_DEMO_MODE=false`). Deferred
hardening includes denormalizing `organization_id` onto child entities or
enforcing a single project-join query helper.

## Data handling and audit

- Audit events record actor attribution, the related entity, a description, a
  timestamp, and non-sensitive structured metadata. Raw IP addresses and user
  agents are never stored; only optional hashes may be recorded.
- Responses and audit metadata never include full extracted page text, full
  applicant response text, full comment-letter text, a raw filesystem path, a
  storage key, a signed URL, a token, a password, a password hash, or any
  credential.

## Dependency and supply-chain policy

Production and full-tree dependency audits run as CI release gates. Any accepted
finding requires a documented owner and expiry in
`docs/internal/DEPENDENCY_REMEDIATION.md`. The dependency security policy is
recorded in `docs/adr/0008-dependency-security-policy.md`.

## Known limitations

- Local authentication only; no SSO and no hardened enterprise session system.
  No enterprise tenant isolation claims.
- No applicant-facing portal; applicant responses are reviewer-entered records
  kept for reviewer review.
- Durable object storage must be configured in deployment; the default local
  provider is for development only. No malware scanning yet.
- Session renewal means signing in again after expiry.
