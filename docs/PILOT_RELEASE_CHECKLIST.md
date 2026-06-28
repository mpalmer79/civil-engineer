# Pilot Release Checklist

A step-by-step verification before sharing the site with design-partner firms.
It pairs with `docs/RELEASE_READINESS.md`. No secret values appear here; use your
own deployment's configuration.

## Required environment variables

Backend:

- `AUTH_SECRET_KEY` - secret used to sign bearer tokens. Set a strong unique
  value in any shared or deployed environment.
- `DATABASE_URL` - database connection string (SQLite for the pilot).

Frontend:

- `NEXT_PUBLIC_API_BASE_URL` - the backend origin only (no `/api/v1` path). The
  frontend appends the API paths itself.

## Optional environment variables

- `CORS_ORIGINS` / `FRONTEND_ORIGIN` - allowed browser origins for the API.
- `AUTH_DEMO_MODE`, `AUTH_ALLOW_PUBLIC_DEMO`, `AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS`
  - demo posture. For production tenant data, set
  `AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS=true` and `AUTH_DEMO_MODE=false`.
- `AI_PROVIDER`, `AI_ENABLE_LIVE_CALLS`, `AI_MODEL`, `OPENAI_API_KEY` - live AI is
  off by default. All are required together to enable live calls; leave unset to
  keep the deterministic mock provider.
- `STORAGE_PROVIDER`, `LOCAL_STORAGE_DIR`, and the `OBJECT_STORAGE_*` keys -
  document storage. Local storage is the default.
- `CAD_UPLOAD_DIR`, `CAD_MAX_UPLOAD_BYTES`, `PROJECT_UPLOAD_DIR` - upload handling.

## Local development startup

1. Backend: from `backend/`, install `requirements.txt`, then run the FastAPI app
   (for example `uvicorn app.main:app --reload`). Startup seeds Brookside Meadows.
2. Frontend: from the repo root, `npm install`, then `npm run dev`.
3. Set `NEXT_PUBLIC_API_BASE_URL` to the backend origin (default
   `http://localhost:8000`).

## Deployment startup

1. Deploy the backend with `AUTH_SECRET_KEY` and `DATABASE_URL` set.
2. Deploy the frontend with `NEXT_PUBLIC_API_BASE_URL` pointing at the backend
   origin, and redeploy the frontend after the backend URL changes.
3. Confirm `CORS_ORIGINS` includes the frontend origin.

## Backend health check

- `GET /health` returns `{ status: "ok", service, version, demo_mode }`. No
  secrets.
- `GET /api/v1/readiness` returns the sanitized readiness summary (database,
  config, storage) for a deeper operational check.

## Frontend health check

- Load `/` and confirm the homepage renders with media.
- Confirm the page does not error when the backend is unavailable (it degrades to
  seeded copy and media fallbacks).

## Public routes to verify

- `/` (homepage)
- `/guided-demo`
- `/pilot`
- `/start-here`
- `/projects` (demo-aware; shows Brookside without a login)

## Protected routes to verify

- `/workspace` - shows a sign-in prompt when signed out, the workspace home when
  signed in.
- `/workspace/settings` - placeholder sections marked "coming later".
- `/admin/pilot-requests` - unauthorized state when signed out, forbidden state
  for a signed-in non-admin, the list for an organization admin.

## Demo route verification

- From `/guided-demo`, confirm the five steps link to real Brookside surfaces and
  the proof counts render (or degrade to qualitative cards).
- Open `/projects/proj_brookside_meadows/command-center`, `/traceability`, and
  `/review-packets` without a login and confirm they load.

## Pilot request verification

- Submit the `/pilot` form and confirm the honest success state appears.
- Confirm a forced failure (backend down) shows an error and not a fake success.

## Pilot admin verification

- Signed out: `GET /api/v1/pilot-requests` returns 401; the admin page shows the
  sign-in state.
- Signed in as a non-admin: returns 403; the admin page shows the forbidden
  state.
- Signed in as an organization admin: returns 200; the admin page lists requests.

## Tenant guard verification

- Run `backend/tests/test_tenant_isolation.py` and
  `backend/tests/test_guard_coverage.py`.
- Confirm a signed-in non-member receives 403 on another project's routes, the
  owner receives 200, and the Brookside demo stays readable anonymously.

## Rollback notes

- The pilot adds new read-only/operator surfaces and access guards; it changes no
  analytical behavior. To roll back, redeploy the previous build. Pilot request
  records persist in the database and are unaffected by a frontend rollback.

## Known limitations

- SQLite database; no Postgres migration.
- Local accounts only; no password reset, team invitations, or SSO.
- Billing is not active.
- Live AI is disabled by default.
- The anonymous demo-reviewer fallback must be turned off before hosting real
  tenant data.
