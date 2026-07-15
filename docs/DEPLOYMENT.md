# Deployment

This is the canonical deployment reference for Civil Engineer AI. It covers the
Railway two-service topology, the production database and migrations, deployment
hardening and observability, and environment validation. It folds in the former
Railway deployment guide, production database, deployment hardening, and
environment validation documents.

## Topology

Civil Engineer AI deploys on Railway as one project with two services that build
from the same repository:

- Service 1: the FastAPI backend, root directory `backend`.
- Service 2: the Next.js frontend, root directory the repository root.

The two services connect through two mirrored settings: the frontend
`NEXT_PUBLIC_API_BASE_URL` points at the backend public origin, and the backend
`FRONTEND_ORIGIN` points at the frontend public origin. There is no shared state
between them other than the HTTP API. A visible backend connection banner on the
frontend home page reports whether the backend is reachable.

## Backend service

- Source: this repository, root directory `backend`, where `requirements.txt` and
  `railway.json` live.
- Builder: Nixpacks detects the Python project from `requirements.txt`.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (set in
  `backend/railway.json`).
- Healthcheck path: `/health`.

Verify the backend after deploy by opening these URLs against the backend origin:

- `<backend-origin>/health` returns the health JSON (status, service name,
  version, demo mode).
- `<backend-origin>/api/v1/readiness` returns a safe readiness summary. It uses
  operational status labels only and never returns secrets.
- `<backend-origin>/api/v1/projects/proj_brookside_meadows` returns the seeded
  Brookside Meadows project payload.

A `404` on the backend root `/` is not necessarily a failure: the backend serves
no page at `/`. If `/health` and the `/api/v1` routes respond, the backend is
working. Check `/health` and an `/api/v1` route before concluding the backend is
down.

Backend service variables include `CORS_ORIGINS`, `FRONTEND_ORIGIN`,
`CAD_UPLOAD_DIR`, `MAX_CAD_UPLOAD_BYTES`, and `DEMO_MODE`. Local defaults work
without them; a deployment sets the ones it needs. `FRONTEND_ORIGIN` is the
deployed frontend URL and, when set, is added to the allowed CORS origins.

## Frontend service

- Source: this repository, root directory the repository root.
- Build command: `npm ci && npm run build`.
- Start command: `npm run start -- --hostname 0.0.0.0 --port $PORT` (set in the
  root `railway.json`).

Set one frontend service variable:

```
NEXT_PUBLIC_API_BASE_URL=https://your-backend-service.up.railway.app
```

`NEXT_PUBLIC_API_BASE_URL` is the public origin of the backend service only, with
no trailing slash and no `/api` or `/api/v1` path. The frontend API modules
append `/api/v1/...` paths themselves, so adding a path here would produce a
double prefix and break every call. Locally the default is `http://localhost:8000`.

### Frontend redeploy and stale builds

The frontend is a Next.js build, so the content a visitor sees comes from
whatever commit Railway last built, not automatically from the latest `main`.

- The live frontend must be redeployed after `NEXT_PUBLIC_API_BASE_URL` changes.
  The value is compiled into the build, so a changed backend URL only takes
  effect after a new frontend deploy.
- The frontend build can appear stale if Railway does not redeploy from the
  latest `main`. If the live homepage or navigation does not match the current
  `main` branch, trigger a fresh deploy of the frontend service from the latest
  commit.
- `NEXT_PUBLIC_API_BASE_URL` must be the backend origin only. Do not include
  `/api/v1` in it.

After redeploying, confirm the live site against the checklist in
`docs/OPERATIONS.md`.

## Object storage and credentials

Project document uploads are managed through a storage provider abstraction with
two options:

- Local storage (`STORAGE_PROVIDER=local`, the default): uploads are stored under
  `LOCAL_STORAGE_DIR` on the backend file system. This is for development and is
  not durable across redeploys without a mounted volume.
- S3-compatible object storage (`STORAGE_PROVIDER=s3`, recommended for
  deployment): configure `OBJECT_STORAGE_BUCKET`,
  `OBJECT_STORAGE_ACCESS_KEY_ID`, `OBJECT_STORAGE_SECRET_ACCESS_KEY`, and the
  optional endpoint, region, and path-style settings.

Object storage credentials are read only when `STORAGE_PROVIDER=s3`. They are
backend service variables only. Never put them in the frontend or in any
`NEXT_PUBLIC_*` variable. The frontend downloads files through the
access-controlled backend route and never holds storage credentials.

## Production database and migrations

SQLite is the default for local development, tests, and the pilot prototype.
Postgres is required for production SaaS. The provider is selected from
`DATABASE_URL`, the legacy `postgres://` scheme is normalized automatically, and
the schema is managed with Alembic migrations. In strict production mode
(`APP_ENV=production`) the backend refuses to start on SQLite.

- Apply migrations with `alembic upgrade head` from `backend/`; check status with
  `alembic current`. The initial migration is `0001_initial_schema`; later
  migrations add the auth, billing, and usage tables and the webhook idempotency
  table.
- CI validates that the migration graph has exactly one head.

## Hardening, observability, and environment validation

- Public health (`/health`) and readiness (`/api/v1/readiness`) checks expose
  only safe operational status. Readiness confirms database connectivity with a
  `SELECT 1`, required configuration presence, migration control state, and
  storage provider readiness. It reports the deployment mode (`app_env`), the
  database provider class (`sqlite`, `postgres`, or `other`), and the migration
  status. The auth secret is reported as `needs_operator_review` when it equals
  the development default, and its value is never returned.
- Detailed diagnostics are admin-gated: the environment diagnostic
  (`/api/v1/diagnostics/environment`) requires an organization admin, and the
  storage diagnostic requires an authenticated user. They report only whether
  each setting is configured, never a secret value, the database URL, object
  storage credentials, a token, a signed URL, or a raw path.
- A safe structured logger masks secret-like keys to `[redacted]` and path-like
  keys to `[set]`. The startup configuration log records provider names and flags
  with no secrets.
- The frontend Deployment Status page at `/deployment-status` surfaces the same
  safe operational status.

Diagnostics are operational indicators only. A readiness, environment, or storage
status reports whether a service is available and whether configuration is
present. It is not an engineering or compliance determination.

## Common deployment problems

- The frontend points at the frontend URL instead of the backend URL. Set
  `NEXT_PUBLIC_API_BASE_URL` to the backend public origin.
- `NEXT_PUBLIC_API_BASE_URL` includes an `/api/v1` path. It must be the backend
  origin only; the connection banner detects and reports this.
- The backend service was built from the wrong root directory. It must be
  `backend`.
- Local storage is used in a deployment without a mounted volume or object
  storage, so uploads and the SQLite database are recreated on each redeploy.
- The frontend was deployed before the backend environment was fixed. Redeploy
  the frontend after changing `NEXT_PUBLIC_API_BASE_URL`.
- Object storage credentials were placed in the frontend by mistake. They are
  backend-only. Never put them in the frontend.
