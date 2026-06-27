# Production Foundations Sprint 10: Production Deployment Hardening, Environment Validation, and Observability

## What Sprint 10 adds

Sprint 10 adds the first deployment readiness and observability layer to Civil
Engineer AI. Before this sprint, the platform could run locally and on Railway,
but an operator had no built-in way to confirm that a deployment was configured
correctly, that the backend was reachable, that storage was ready, or that the
frontend was pointed at the right backend origin. Sprint 10 adds:

- An environment validation service that inspects backend configuration and
  reports a sanitized diagnostic summary, never exposing secret values.
- Public health and readiness checks that report liveness and a sanitized
  readiness summary across database, authentication, and storage.
- Admin-gated environment and storage diagnostics that report operational status
  per configuration item with remediation hints, never returning secret values.
- A public frontend-connection diagnostic and a public security-boundary
  diagnostic that explain how the frontend should reach the backend and restate
  that diagnostics are operational indicators only.
- A safe structured logger with a redaction helper, plus a safe startup
  configuration log event that records provider names and flags without secrets.
- A Deployment Status page in the frontend, an updated backend status banner that
  detects a wrongly configured base URL, and a `verify:live` script that checks a
  running deployment from the outside.

All diagnostics are computed at request time from existing configuration. No new
persistent table was added. The same environment validation service backs the
readiness check, the environment diagnostics, and the storage diagnostics, so the
same sanitized operational status appears everywhere.

## How it builds on Sprints 1 through 9

Sprint 10 reads, but does not change, the foundations produced by earlier
sprints:

- Sprint 1 project records, documents, findings, and audit events.
- Sprint 2 PDF page indexing.
- Sprint 3 evidence retrieval candidates.
- Sprint 4 checklist evidence status.
- Sprint 5 authentication and access control, which gates the detailed
  diagnostics behind an organization admin and an authenticated user.
- Sprint 6 storage provider abstraction, whose provider name and readiness are
  reported at a safe summary level only (no credentials, no bucket values, no
  paths).
- Sprint 7 response matrix and resubmittal records.
- Sprint 8 reviewer response packages.
- Sprint 9 reviewer and organization dashboards.

Sprint 10 adds an operational status layer on top of this data. It does not
introduce new review outcomes and does not change any existing workflow.

## Why deployment hardening matters before deeper product expansion

As Civil Engineer AI moves from a controlled portfolio demo toward real-world
review-support use, a wrong environment variable can quietly break a deployment.
A frontend pointed at the wrong backend origin, a missing database URL, a storage
provider with no bucket configured, or an auth secret left at the development
default can all produce confusing failures that are hard to diagnose from the
outside.

Sprint 10 makes these conditions visible. An operator can open the readiness
check or the Deployment Status page and see, in safe operational terms, what is
ready, what is missing, and what needs operator review. This reduces guesswork
before the platform takes on deeper product expansion. It is operational
hardening, not an engineering decision layer.

## What remains demo-only

Brookside Meadows remains a seeded public demo fixture and is fully preserved.
The demo mode flag is reported by the health and readiness checks as safe runtime
metadata. Seeded demo users exist for the local demo only with documented local
passwords. Diagnostics report demo-related flags (demo mode, public demo allowed,
seed demo users) as operational status, never as secrets.

## What remains out of scope

Sprint 10 does not add live AI calls, OCR, DWG parsing, GIS or Bluebeam
integrations, automated engineering calculations, geometry or design validation,
final approval workflows, enterprise SSO, a full applicant portal, or billing. It
does not add external application performance monitoring, external error
aggregation, distributed tracing, or any third-party observability service. It
does not rewrite the architecture, remove Brookside Meadows, or weaken
authentication, access control, audit, or storage enforcement.

## How environment validation works

The environment validation service in
`backend/app/services/environment_validation_service.py` inspects the backend
service configuration and produces a list of diagnostic items. Each item reports
a category, a configuration key, an operational status, a severity, a message, a
required flag, a configured flag, a public hint, and a remediation hint. The
service never returns a secret value. For each environment variable it reports
only whether the value is present and whether it looks ready, not the value
itself.

The service validates backend service variables across application, database,
authentication, storage, object storage, public demo, cors, deployment, and
frontend integration categories. For example, it flags a missing required
database URL as `missing_required` with critical severity, an auth secret left at
the development default as `needs_operator_review`, and an unset optional value as
`missing_optional`. Path-like values such as the local storage directory are
never exposed; the diagnostic reports only that a path is set.

The service exposes the following functions: `validate_environment` for the full
admin environment diagnostic, `get_readiness` for the sanitized public readiness
summary, `get_storage_diagnostics` for the storage diagnostic, and
`get_frontend_config_diagnostics` and `get_security_boundary_diagnostics` for the
public guidance and boundary diagnostics.

## How health and readiness checks work

The `GET /health` endpoint is a lightweight liveness check. It is public, returns
no secrets, and reports a status, the service name, a product version, and the
demo mode flag. Railway uses it to confirm the service is live.

The `GET /api/v1/readiness` endpoint is a public, sanitized readiness check. It
returns the same safe runtime metadata plus a list of checks, where each check
reports a category, an operational status, and a message. Readiness checks
database connectivity with a `SELECT 1`, confirms that required configuration is
present, and reports storage provider readiness. The readiness response is
deliberately sanitized so it can stay public without exposing configuration
detail. It reports operational status only, never a secret value, a path, or a
credential.

## How storage diagnostics work

The `GET /api/v1/diagnostics/storage` endpoint requires an authenticated user. It
reports the storage provider name, whether storage is configured, an operational
status, a message, and a list of storage items. It never returns credentials.
Bucket information is limited to configured or not-configured, and no paths or
keys are returned. For the local provider it reports readiness without exposing
the storage directory path. For the S3-compatible provider it reports whether the
required backend-only credentials and bucket are configured, without returning
their values.

## How frontend backend-connection diagnostics work

The `GET /api/v1/diagnostics/frontend-config` endpoint is public. It reports the
API prefix the backend serves, that the frontend should be configured with the
backend origin only, the name of the frontend environment variable, and a list of
guidance strings. This makes the most common deployment misconfiguration easy to
diagnose: the frontend `NEXT_PUBLIC_API_BASE_URL` must be the backend origin only,
with no `/api/v1` path, because the frontend appends `/api/v1` itself.

On the frontend, the Deployment Status page at `app/deployment-status/page.tsx`
reads the readiness and storage diagnostics through `lib/api/diagnostics.ts` and
shows the backend origin, the readiness summary, storage status, and
troubleshooting guidance. The updated backend status banner detects when the
configured base URL wrongly includes `/api/v1` and surfaces that as a
configuration check failure so an operator can fix it quickly.

## How to test locally and on Railway

Locally:

1. Start the backend and frontend.
2. Open `http://localhost:8000/health` and confirm the liveness JSON.
3. Open `http://localhost:8000/api/v1/readiness` and confirm the readiness
   summary with database, authentication, and storage checks.
4. Sign in as an organization admin and open
   `http://localhost:8000/api/v1/diagnostics/environment` to confirm the
   environment diagnostic items.
5. Open the frontend `/deployment-status` page and confirm it shows the backend
   origin, readiness, storage status, and troubleshooting.

On Railway:

1. Deploy the backend and frontend services as described in the Railway
   deployment guide.
2. Confirm the backend `/health` and `/api/v1/readiness` respond against the
   deployed backend origin.
3. Run `npm run verify:live` to check the frontend homepage, the backend
   `/health`, the backend `/api/v1/readiness`, and that the backend URL has no
   `/api/v1` path. The script prints labels of ok, warning, unavailable, or needs
   operator review.

Automated gates: run the backend suite with `pytest` (the environment validation
service, the diagnostics routes, and the redaction helper have tests) and the
frontend gates with `npm run typecheck`, `npm run lint`, `npm test`, and
`npm run build`.

## Professional boundary note

The Sprint 10 diagnostics are operational indicators only. A readiness status, an
environment diagnostic, or a storage status reports whether a service is
available and whether configuration is present. It does not approve plans, certify
compliance, declare a project safe, validate design, resolve an issue, or make any
engineering decision. Diagnostics describe the runtime operational status of the
deployment, not the review-support outcome of any project. Civil Engineer AI
remains review-support only and does not replace a licensed Professional Engineer.
