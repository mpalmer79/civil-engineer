# Deployment Hardening and Observability

This document describes the operational readiness and observability layer added in
Production Foundations Sprint 10. It explains how Civil Engineer AI is deployed as
two Railway services, how the frontend reaches the backend, what is safe to log,
and the limits of the built-in diagnostics.

## Operational readiness goals

The goal of this layer is to make deployment configuration visible in safe
operational terms. An operator should be able to answer these questions without
reading secrets:

- Is the backend live and reachable.
- Is the database connected.
- Is the auth secret ready or still at the development default.
- Is the storage provider ready, and is its required configuration present.
- Is the frontend pointed at the correct backend origin.
- What configuration is missing or needs operator review.

These are operational indicators only. They report runtime status, not any
engineering or compliance determination.

## Railway frontend and backend service split

Civil Engineer AI deploys as one Railway project with two services:

- A FastAPI backend service, with its root directory set to the `backend` folder.
- A Next.js frontend service, with its root directory set to the repository root.

The two services connect only through HTTP. The frontend calls the backend
through a single public environment variable, and the backend allows the frontend
origin through a single environment variable. There is no shared state between
them other than the API.

## Backend origin rules

The frontend must be configured with the backend origin only. The backend serves
its API under the `/api/v1` prefix, and the frontend API modules append
`/api/v1/...` paths themselves. If the configured base URL already includes
`/api/v1`, every call produces a double prefix and breaks. The
`GET /api/v1/diagnostics/frontend-config` endpoint and the updated backend status
banner both detect and explain this condition.

## Frontend public env var behavior

`NEXT_PUBLIC_API_BASE_URL` is a frontend service variable. It is compiled into the
Next.js build and is the public origin of the backend service only, with no
trailing slash and no `/api` or `/api/v1` path. Because it is compiled into the
build, a changed backend URL only takes effect after the frontend service is
redeployed. The backend never reads this variable.

Any variable prefixed with `NEXT_PUBLIC_` is exposed to the browser. Only
non-secret values belong in a `NEXT_PUBLIC_` variable.

## Backend-only secrets

Secrets stay on the backend service. These are backend service variables only and
must never be placed in any `NEXT_PUBLIC_` variable:

- `AUTH_SECRET_KEY`
- `OBJECT_STORAGE_ACCESS_KEY_ID`
- `OBJECT_STORAGE_SECRET_ACCESS_KEY`
- `DATABASE_URL`

The frontend reaches storage and protected data only through the access-controlled
backend routes. It never holds storage credentials, the auth secret, or the
database URL.

## Storage provider readiness

The storage diagnostic reports the storage provider name and whether its required
configuration is present. For the local provider it reports readiness without
exposing the storage directory path. For the S3-compatible provider it reports
whether the required bucket and backend-only credentials are configured, reported
as configured or not-configured, without returning bucket values, paths, keys, or
credentials. Object storage credentials are read only when `STORAGE_PROVIDER=s3`.

## Auth secret readiness

The environment validation service reports whether `AUTH_SECRET_KEY` is present.
If it equals the development default `dev-only-insecure-change-me`, the diagnostic
reports `needs_operator_review` so an operator knows the development default is
still in place. The diagnostic never returns the value of the secret.

## Database connectivity

The readiness check confirms database connectivity by running a `SELECT 1`. It
reports the outcome as an operational status and a message. It reports the kind of
database in safe terms only and never returns the database URL or any credential
embedded in it.

## Safe logging

`backend/app/core/logging.py` provides a safe structured logger (`get_logger` and
`log_event`) and a `redact()` helper. The redaction helper masks secret-like keys
to `[redacted]` and path-like keys to `[set]`, so a log event records that a value
exists without recording the value itself. The backend writes a safe
`startup_configuration` event at startup with provider names and flags and no
secrets.

Safe to log:

- the storage provider name
- demo flags (demo mode, public demo allowed, seed demo users)
- the database kind in safe terms
- a readiness outcome (an operational status)

Never log:

- tokens
- passwords
- password hashes
- raw uploaded content
- full extracted page text
- full applicant response text
- full comment letter text
- raw storage paths
- storage keys
- signed URLs
- object storage credentials

## Diagnostic limitations

The Sprint 10 diagnostics are intentionally lightweight and local:

- They run inside the backend process at request time. There is no external
  application performance monitoring, no external error aggregation service (for
  example, no Sentry), and no distributed tracing (for example, no
  OpenTelemetry).
- They report operational status only. They do not store metrics over time and do
  not raise alerts.
- They make no SOC 2 or formal compliance claim. They are an operator-facing
  readiness aid, not an audited monitoring system.
- They are operational indicators only. A readiness or diagnostic status does not
  approve plans, certify compliance, declare a project safe, validate design, or
  make any engineering decision.
