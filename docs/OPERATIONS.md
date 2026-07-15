# Operations

This is the canonical operations reference for Civil Engineer AI. It covers
release readiness, the pilot request and operator workflow, account lifecycle
email, billing and usage, and the live-site verification checklist. It folds in
the former release-readiness, pilot-checklist, pilot-operations,
design-partner-outreach, billing, Stripe, email, and live-site verification
documents.

Everything here is review-support operations. No operational status, plan, or
subscription state implies a review outcome, approval, certification, or
compliance. A human reviewer remains responsible for every finding.

## Release readiness

Civil Engineer AI is ready for an early design-partner pilot, not for
production multi-tenant SaaS. The Brookside Meadows sample project
(`proj_brookside_meadows`) is a seeded review-support demo marked `demo_public`,
so it stays readable without a login. The homepage, `/guided-demo`,
`/start-here`, and the Brookside surfaces run on this seeded data plus CAD
findings produced by really parsing a bundled sample DXF.

### Production-posture environment profile

For a public pilot deployment, set these backend flags so real project data is
protected while the public demo keeps working:

- `AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS=true`: a real project rejects anonymous
  access (401) and non-member access (403).
- `AUTH_DEMO_MODE=false`: turns off the anonymous demo-reviewer fallback for real
  projects.
- `AUTH_ALLOW_PUBLIC_DEMO=true`: keeps the Brookside demo project readable
  without a login.

For a production SaaS deployment, also set `APP_ENV=production` and point
`DATABASE_URL` at a Postgres database, then run `alembic upgrade head`. In
production mode the backend refuses to start on SQLite. SQLite stays the default
for local development and the pilot prototype. See `docs/DEPLOYMENT.md`.

`backend/tests/test_release_posture.py` pins this behavior: under these flags the
Brookside demo stays anonymously readable, a real project rejects anonymous (401)
and non-member (403) access, the owner reads it (200), public pilot submission
still works, and the pilot admin list stays protected.

### Public route allowlist

Only these surfaces are intended to be reachable without a login: `/`,
`/guided-demo`, `/pilot`, `/start-here`, the Brookside Meadows demo project
surfaces used by the guided demo, `/health` and `/api/v1/readiness`, and static
assets under `public/`. Everything else is protected, including `/workspace`,
`/workspace/settings`, `/admin/pilot-requests`, all real tenant projects and
their project-owned API routes, and the pilot request admin and export APIs.
The public route allowlist is enforced by the access guards and the auth posture
flags, not by a separate route table, so a new project-owned route is protected
by default.

### Required environment variables

Backend:

- `AUTH_SECRET_KEY`: secret used to sign bearer tokens. Set a strong unique value
  in any shared or deployed environment.
- `DATABASE_URL`: database connection string. SQLite is acceptable for local
  development, tests, and the pilot prototype; production SaaS requires a Postgres
  URL.
- `APP_ENV`: deployment mode (`development`, `pilot`, or `production`). In
  `production` the backend refuses to start on SQLite.

Frontend:

- `NEXT_PUBLIC_API_BASE_URL`: the backend origin only, with no `/api/v1` path. The
  frontend appends the API paths itself. Example:
  `NEXT_PUBLIC_API_BASE_URL=https://your-backend-service.up.railway.app`.

### Current limitations

- Database: SQLite for local development and tests; Postgres required for
  production SaaS. Alembic migrations are in place.
- Auth: local accounts and bearer tokens. Password reset and team invitation
  flows are implemented; email confirmation and SSO are not.
- Billing: implemented but inactive until configured. No payment is collected
  until Stripe keys are set. Usage limits are advisory by default and enforceable
  for selected categories.
- Live AI: disabled by default. The default provider is a deterministic mock.
- Capability scope: real DXF parsing (ezdxf) and PDF text-layer indexing (pypdf)
  only. No OCR, DWG, GIS, computer vision, or vector search. See `docs/PRODUCT.md`
  for the canonical capability wording.

### Release recommendation

Ready for a design-partner pilot: share the public site and guided demo, collect
pilot requests, and run scoped conversations. Not ready to host real,
multi-tenant customer data until the production-posture items above are
addressed. Treat this as a pilot-ready prototype.

## Pilot request and operator workflow

`/pilot` is a public design-partner request form (name, work email, firm, role,
project type, primary pain, interest level, optional notes, and a sample-package
checkbox). It collects no file uploads. Submissions persist via
`POST /api/v1/pilot-requests`, show an honest success state, and never claim an
email was sent. On failure the form shows an error and never fakes success.

A signed-in organization admin reviews submitted requests at
`/admin/pilot-requests`, backed by the admin-gated `GET /api/v1/pilot-requests`.
Anonymous visitors get an unauthorized state and a signed-in non-admin gets a
forbidden state; neither sees any data. Submitted requests carry an operator
pipeline status (`new`, `contacted`, `qualified`, `active_pilot`, `closed`,
`rejected`), operator-only internal notes, and a last-contacted timestamp. An
admin can filter, search, update status, save notes, and export a CSV. Internal
notes are never returned by the public submission endpoint. A dedicated
pilot-operator role was deliberately not added; organization admin is the
operator gate.

Outreach to design partners leads with the resubmittal-cost argument: run a
package through pre-submittal QA and catch the review-support issues a municipal
reviewer would catch, before the package goes out. Offer a scoped
design-partner pilot for firms willing to provide real usage and a quote.

## Account lifecycle email

Real email delivery is available for account lifecycle only (password reset and
team invitation). It carries no review-support content. The mailer abstraction
(`backend/app/services/mailer.py`) selects a provider with `EMAIL_PROVIDER`:

- `noop` (default): records a redacted delivery log and sends nothing, keeping
  local development and tests free of any email service.
- `smtp`: delivers real email through a configured SMTP server using the Python
  standard library, so no third-party dependency is required.

The mailer never logs an SMTP credential, a reset token, an invitation token, a
full link, an email subject, or an email body. It logs only the provider, the
message category, a redacted recipient, and whether a message was sent. A raw
token appears only inside the reset or invitation link in the delivered email.
Reset and invitation tokens are stored only as a one-way hash, expire, and are
single-use.

Configuration (backend-only): `EMAIL_PROVIDER`, `EMAIL_FROM`,
`APP_PUBLIC_BASE_URL`, and the `EMAIL_SMTP_*` settings. Before onboarding real
users, set `EMAIL_PROVIDER=smtp` and the SMTP settings, set `APP_PUBLIC_BASE_URL`
to the deployed frontend origin, and keep `AUTH_EXPOSE_DEV_TOKENS` off (it is
forced off in production regardless).

## Billing and usage

A plan or subscription status is an account-posture label only. It never implies
a review outcome, approval, certification, or compliance.

### Stripe status: configured by environment

Stripe checkout and webhooks are implemented and become active when configured.
Stripe is inactive until configured, and no real payment is processed until the
Stripe settings are set. Until then the billing UI and API report an honest
inactive state.

- `billing_enabled` is true only when `STRIPE_SECRET_KEY` is set. It is false by
  default.
- Checkout (`POST /api/v1/organizations/{organization_id}/billing/checkout`)
  requires an organization admin, creates a Stripe Checkout session for the
  professional plan when fully configured, and otherwise returns an honest
  `available: false` response with no checkout URL.
- The webhook endpoint (`POST /api/v1/billing/webhook`) verifies the Stripe
  signature (standard-library HMAC-SHA256, testable without the SDK) and processes
  subscription events idempotently. Each processed event id is recorded in
  `billing_events`; a duplicate delivery is ignored. No Stripe secret, signature,
  or raw payload is stored.

The environment variables `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
`STRIPE_PRICE_PROFESSIONAL`, `STRIPE_SUCCESS_URL`, `STRIPE_CANCEL_URL`, and
`STRIPE_TEST_MODE` are read backend-only. None are required for local development
or tests, and no secret is exposed to the frontend. `billing_mode` is
`inactive`, `test`, or `live`, and never leaks a secret.

### Usage limits: advisory by default

Usage is metered internally as an append-only ledger (`usage_events`) per
organization. No usage record carries file content, document text, or any
secret. Usage limits are advisory by default: usage is tracked and surfaced with
warning states, but actions are not hard-blocked.

Enforcement is controlled by `USAGE_ENFORCEMENT_ENABLED` (default false). Usage
is advisory by default and enforceable for selected categories. When enabled,
`project_created`, `document_uploaded`, and `review_packet_generated` are
hard-enforced for real organizations. When an enforced action is at or over its
plan limit, the API returns `402` with a `limit_exceeded` detail (category,
limit, used, plan) before any mutation, so nothing is written. The public
Brookside demo and the seeded demo organization (`org_internal_demo`) are
never enforced regardless of the flag.

Team invitation and password-reset lifecycle is covered in `docs/SECURITY.md`.
No surface claims an active subscription unless the backend reports one, and the
checkout call to action appears only when checkout is available.

## Logging and observability

The backend emits structured, secret-safe log events through a single named
logger (`civil_engineer`). Every event is `key=value` text with secret-like and
path-like fields redacted before anything is written. Logging is standard
library only: no external APM, Sentry, or OpenTelemetry.

### Request correlation

Every request is assigned a correlation id. If the caller sends a safe
`X-Request-Id` header it is reused; otherwise a fresh id is generated. The id is:

- bound to the request context and merged into every log event for that request,
- echoed on the response `X-Request-Id` header (exposed to browser clients), and
- written onto every audit row created during the request, so the audit trail
  joins to the access logs for a single request.

One `request_completed` event per request records the method, route, status, and
duration. A resolved signed-in user id is bound to the context after
authentication so later events and audit rows share the same attribution. To
trace an issue, take the `request_id` from the client response or a support
report and grep the logs for it.

### Error handling

Uncaught exceptions are caught by a global handler that returns a generic
`{"detail": "Internal server error.", "request_id": ...}` with status 500. The
exception type and route are logged server side with the correlation id; the
exception message, stack trace, and internal detail are never sent to the
client. Typed route errors keep their specific status codes and messages.

### Configuration

- `LOG_LEVEL` sets verbosity (DEBUG, INFO, WARNING, ERROR). An unknown value
  falls back to INFO rather than failing startup. Default INFO.
- `PDF_MAX_PAGES` bounds how many pages are indexed inline per PDF so a large or
  hostile file cannot exhaust the request thread. Pages beyond the cap are left
  for reviewer follow-up and the document is flagged `indexed_partial_needs_review`.
  Default 500; set 0 to disable the cap.

## Background processing worker

File processing (PDF page indexing and DXF metadata parsing) can run inline on
the request thread, or be handed to a background worker for large files and
higher load. The worker is optional: small and development deployments can rely
on the synchronous routes and need not run it. See
`docs/adr/0012-background-job-queue.md`.

### How it works

- The async endpoints (`POST .../index-pdf/jobs`, `POST .../parse/jobs`) enqueue
  a row in the `processing_jobs` table and return `202 Accepted` with a job id.
- The worker process claims queued jobs, runs the same processing the
  synchronous routes run, and records success or failure. Job claiming is safe
  under multiple concurrent workers.
- A transient failure retries with exponential backoff up to `WORKER_MAX_ATTEMPTS`.
  A permanent fault (an unreadable or missing file) fails immediately with no
  retry. A job whose worker dies is reclaimed after `WORKER_STALE_SECONDS`.
- Each job carries the correlation id of the request that enqueued it, so its
  audit rows and logs trace back to that request.
- Poll `GET /api/v1/projects/{project_id}/jobs/{job_id}` for status, or
  `GET /api/v1/projects/{project_id}/jobs` for a project's recent jobs.

### Running the worker

Run one or more worker processes alongside the API, against the same database:

```
python -m app.worker
```

On Railway, add a second service in the backend directory with the start command
`python -m app.worker` (no health check; it is not an HTTP service). See
`docs/DEPLOYMENT.md`.

### Configuration

- `WORKER_POLL_INTERVAL_SECONDS` (default 2.0): idle poll interval.
- `WORKER_MAX_ATTEMPTS` (default 3): retry ceiling before a job is marked failed.
- `WORKER_RETRY_BACKOFF_SECONDS` (default 30): base for exponential retry backoff.
- `WORKER_STALE_SECONDS` (default 300): lease timeout before a running job is
  reclaimed.

### Monitoring

The worker logs `worker_started`, `job_claimed`, `job_succeeded`,
`job_retry_scheduled`, `job_failed`, and `jobs_reclaimed` events, all with the
correlation id. A rising count of failed jobs or repeated reclaims indicates a
processing or worker-health problem to investigate.

## Live-site verification checklist

Run this checklist after every frontend redeploy to confirm the deployed site
matches the current `main` branch. It confirms discoverability and accurate
messaging, not any engineering outcome.

Live demo URL: https://civil-engineer.up.railway.app/

`NEXT_PUBLIC_API_BASE_URL` must be the backend origin only, for example
`NEXT_PUBLIC_API_BASE_URL=https://your-backend-service.up.railway.app`. Do not
include `/api/v1` in it; the frontend appends the API paths itself.

### Core checks

1. Homepage loads at https://civil-engineer.up.railway.app/.
2. The backend connection banner shows connected.
3. Navigation includes Projects, Dashboard, Reviewer Queue, Rule Packs,
   Organizations, Guided Demo, and Account/Login.
4. `/start-here` loads and shows the recommended demo path and the technical
   foundation section.
5. `/guided-demo` still loads and shows the recommended demo path step cards.
6. `/dashboard` and `/dashboard/queue` load (reviewer dashboard and queue).
7. `/rule-packs` and `/organizations` handle the signed-out state safely.
8. The Brookside Meadows public demo still works.
9. On a common mobile width the demo step cards stack and there is no horizontal
   scrolling. The mobile navigation still auto-collapses after selecting a
   primary or demo-module link.

### Deployment diagnostics checks

10. `/deployment-status` loads and shows backend, readiness, and storage
    sections.
11. Backend health route `/health` returns a status payload.
12. Backend readiness route `/api/v1/readiness` returns a safe status payload
    with allowed status labels only.
13. Storage health is visible on the deployment status page after sign-in and
    shows the provider and configuration status only, never credentials.

### Security and language checks

14. No page shows raw storage paths, storage keys, signed URLs, tokens, the auth
    secret, the database URL, or any other secret.
15. No page claims final approval, compliance, certification, validation, issue
    resolution, or issue closure. Diagnostics show operational status only.
16. The footer and page source do not include generated-by attribution or
    session links.

`NEXT_PUBLIC_API_BASE_URL` stays the backend origin only across the deployment.
The optional script `npm run verify:live -- --frontend <frontend-url> --backend
<backend-origin>` checks the homepage, `/start-here`, `/guided-demo`, the
Brookside Meadows sample project, and `/deployment-status`, plus backend
`/health` and `/api/v1/readiness`. It requires no secrets and prints none.
