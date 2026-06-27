# Environment Validation

This document describes the backend and frontend environment variables that Civil
Engineer AI validates in Production Foundations Sprint 10, the expected Railway
settings, and how to diagnose common misconfigurations. The environment
validation service reports whether each value is present and whether it looks
ready. It never returns a secret value.

## Required backend environment variables

These are backend service variables. A missing required value is reported as
`missing_required` with critical severity.

- `DATABASE_URL`: the database connection string. Backend-only. Never returned by
  value.
- `AUTH_SECRET_KEY`: the signing key for access tokens. Backend-only. If it equals
  the development default `dev-only-insecure-change-me`, it is reported as
  `needs_operator_review` so an operator sets a unique value before real use. The
  value is never returned.

## Optional backend environment variables

These are backend service variables. A missing optional value is reported as
`missing_optional` and does not block readiness on its own.

Authentication and demo behavior:

- `AUTH_TOKEN_EXPIRE_MINUTES`
- `AUTH_DEMO_MODE`
- `AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS`
- `AUTH_ALLOW_PUBLIC_DEMO`
- `AUTH_SEED_DEMO_USERS`

Storage:

- `STORAGE_PROVIDER` (`local` or `s3`)
- `LOCAL_STORAGE_DIR` (the path is never exposed; the diagnostic reports only that
  a path is set)
- `OBJECT_STORAGE_BUCKET`
- `OBJECT_STORAGE_ENDPOINT_URL`
- `OBJECT_STORAGE_REGION`
- `OBJECT_STORAGE_ACCESS_KEY_ID` (backend-only credential, never returned by
  value)
- `OBJECT_STORAGE_SECRET_ACCESS_KEY` (backend-only credential, never returned by
  value)
- `OBJECT_STORAGE_FORCE_PATH_STYLE`
- `OBJECT_STORAGE_SIGNED_URL_EXPIRE_SECONDS`

Deployment and frontend integration:

- `CORS_ORIGINS`
- `FRONTEND_ORIGIN`

When `STORAGE_PROVIDER=s3`, the object storage bucket and credentials become
effectively required for storage readiness. The storage diagnostic reports them as
configured or not-configured without returning their values.

## Frontend environment variables

The frontend uses one public variable:

- `NEXT_PUBLIC_API_BASE_URL`: the public origin of the backend service only, with
  no trailing slash and no `/api` or `/api/v1` path. The frontend appends
  `/api/v1` itself. This variable is compiled into the Next.js build. The backend
  never reads it.

## Forbidden frontend secrets

Any variable prefixed with `NEXT_PUBLIC_` is exposed to the browser. Never put a
secret in a `NEXT_PUBLIC_` variable. In particular, never place these in any
`NEXT_PUBLIC_` variable:

- `AUTH_SECRET_KEY`
- `OBJECT_STORAGE_ACCESS_KEY_ID`
- `OBJECT_STORAGE_SECRET_ACCESS_KEY`
- any other `OBJECT_STORAGE_*` credential
- `DATABASE_URL`

These are backend service variables only. The frontend reaches protected data and
storage through the access-controlled backend routes and never holds credentials.

## Expected Railway settings

On the backend service:

- Root directory set to `backend`.
- Healthcheck path `/health`.
- `DATABASE_URL` set to the backend database.
- `AUTH_SECRET_KEY` set to a unique value (not the development default).
- `FRONTEND_ORIGIN` set to the deployed frontend origin so the backend allows the
  browser origin.
- Storage variables set for the chosen provider. For deployment, set
  `STORAGE_PROVIDER=s3` with the object storage bucket and backend-only
  credentials.

On the frontend service:

- Root directory set to the repository root.
- `NEXT_PUBLIC_API_BASE_URL` set to the backend origin only, with no `/api/v1`
  path.

## Common misconfigurations

- `NEXT_PUBLIC_API_BASE_URL` includes `/api/v1`. The frontend appends `/api/v1`
  itself, so this produces a double prefix and breaks every call. The backend
  status banner and the `GET /api/v1/diagnostics/frontend-config` endpoint detect
  and explain this.
- `NEXT_PUBLIC_API_BASE_URL` points at the wrong backend, or has a trailing slash.
  Set it to the backend origin only.
- `FRONTEND_ORIGIN` not set on the backend, so the browser origin is not allowed
  and calls are blocked by CORS.
- `AUTH_SECRET_KEY` left at the development default. The environment diagnostic
  reports `needs_operator_review`.
- `STORAGE_PROVIDER=s3` without a bucket or credentials. The storage diagnostic
  reports the missing required items.
- `DATABASE_URL` missing. The readiness check reports the database as unavailable
  and the environment diagnostic reports `missing_required`.

## How to fix stale frontend builds

`NEXT_PUBLIC_API_BASE_URL` is compiled into the Next.js build, so a changed value
only takes effect after the frontend service is redeployed. After changing
`NEXT_PUBLIC_API_BASE_URL`, redeploy the frontend service from the latest commit
so the new value is built in. If the live frontend does not match the current
backend, trigger a fresh frontend deploy.

## How to verify the backend origin is correct

Confirm that `NEXT_PUBLIC_API_BASE_URL` is the backend origin only, with no
`/api/v1` path:

1. Open `GET /api/v1/diagnostics/frontend-config` on the backend and read the
   guidance.
2. Open the frontend `/deployment-status` page and confirm the backend origin and
   readiness summary. The page surfaces a configuration check when the base URL
   wrongly includes `/api/v1`.
3. Run `npm run verify:live` against the deployment. The script checks the
   frontend homepage, the backend `/health`, the backend `/api/v1/readiness`, and
   that the backend URL has no `/api/v1` path, printing labels of ok, warning,
   unavailable, or needs operator review.

These checks report operational status only. They do not approve plans, certify
compliance, or make any engineering determination.
