# ADR 0003: Secure session architecture

Status: Accepted

## Context

The frontend previously stored the backend access token in
`localStorage` under `civil_engineer_auth_token` and attached it as a Bearer
header from browser JavaScript. Any script running in the page (for example
through a future XSS defect or a compromised dependency) could exfiltrate the
token. Cookie-based sessions require CSRF protection that the token-in-header
model did not need.

## Decision

Browser authentication uses a backend-for-frontend (BFF) layer inside the
Next.js app:

1. Session establishment. `POST /api/session/login` and
   `POST /api/session/register` exchange credentials with FastAPI
   (`/api/v1/auth/login`, `/api/v1/auth/register`), then store the returned
   access token in the `ce_session` cookie: `HttpOnly`, `Secure` in
   production, `SameSite=Lax`, `Path=/`, and a max age matched to the backend
   token lifetime (`AUTH_TOKEN_EXPIRE_MINUTES`). The token never appears in a
   response body, a URL, or a log line.
2. Session indicator. A companion `ce_session_active` cookie (not HttpOnly,
   value `1`, no secret content) lets client code skip requests that would
   certainly return 401. It grants nothing by itself.
3. Authenticated requests. In the browser, `API_BASE_URL` resolves to the
   same-origin proxy `/api/backend/[...path]`, which forwards only `/api/*`
   paths to the FastAPI origin, attaches `Authorization: Bearer <token>` from
   the session cookie server-side, and passes upstream status codes through
   unchanged so 401/403/404/422 semantics reach the UI intact. FastAPI remains
   the canonical authorization authority; existing per-project tenant guards
   are unchanged.
4. CSRF protection. Every mutating request through the proxy or the session
   endpoints must pass two independent checks: when an `Origin` header is
   present it must match the request host, and the request must carry the
   custom `x-csrf-protection: 1` header, which a cross-site attacker cannot
   set without a CORS preflight the browser will refuse. `authHeaders()` adds
   the marker to every API call centrally.
5. Logout. `POST /api/session/logout` clears both cookies. Tokens are
   stateless and signed with a 120-minute expiry, so the browser session ends
   when the cookie is gone and any copied token dies at expiry.
6. Public demo access requires no session; unauthenticated proxy requests are
   forwarded without an Authorization header and receive the backend's public
   demo responses.

## Verification

Exercised end to end against the running production build: login without the
CSRF header returns 403; login with it sets both cookies with the expected
flags; `/api/backend/api/v1/auth/me` authenticates from the cookie; the same
call without a cookie returns an explicit 401; a cross-origin mutation is
rejected; logout clears both cookies. Unit tests cover the CSRF gate and the
proxy (`lib/server/__tests__/session.test.ts`,
`app/api/__tests__/backendProxy.test.ts`).

## Consequences

- No credential is readable by browser JavaScript, and no dead
  token-storage compatibility code remains.
- Server-side rendering stays unauthenticated by design; authenticated views
  fetch client-side through the proxy, matching the previous behavior.
- Token renewal currently means signing in again after expiry; a rotation
  endpoint is a documented follow-up rather than a blocker because the expiry
  is short.
