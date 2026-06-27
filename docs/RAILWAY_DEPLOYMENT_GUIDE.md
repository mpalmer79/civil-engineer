# Railway Deployment Guide

This guide describes how to deploy Civil Engineer AI on Railway as one Railway project with two services: a FastAPI backend service and a Next.js frontend service. It uses plain configuration values and Railway dashboard setting descriptions rather than shell commands.

This is a portfolio demo deployment. It uses no authentication, no paid services, no production email, and no external object storage. Uploaded files and the SQLite database live on the service file system and are recreated from seed data on each deploy unless a persistent volume is mounted.

## Overview

One Railway project contains two services that deploy from the same repository:

- Service 1: the FastAPI backend, with its root directory set to the `backend` folder.
- Service 2: the Next.js frontend, with its root directory set to the repository root.

The frontend calls the backend through a single environment variable, and the backend allows the frontend origin through a single environment variable. There is no shared state between the two services other than the HTTP API.

## Service 1: FastAPI backend

### Source and root directory

- Source: this repository.
- Root directory setting: `backend`.

Railway builds the service from the `backend` folder, where `requirements.txt` and `railway.json` live. The `backend/railway.json` file sets the start command and the healthcheck path, so the dashboard does not need them entered by hand.

### Build

- Builder: Nixpacks (the default). Nixpacks detects the Python project from `requirements.txt` and installs the dependencies.

### Start command

The start command runs the existing FastAPI entrypoint and binds to the port Railway provides:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

`$PORT` is provided by Railway at runtime. This same command is set in `backend/railway.json`.

### Healthcheck

- Healthcheck path: `/health`.

The backend exposes a `/health` endpoint that returns a status, the service name, a product version, and the demo mode flag. Railway uses it to confirm the service is live.

### Verifying the backend after deploy

Open these URLs against the deployed backend origin to confirm it is serving the review-support API:

- `https://your-backend-service.up.railway.app/health` returns the health JSON (status, service name, version, demo mode).
- `https://your-backend-service.up.railway.app/api/v1/projects/proj_brookside_meadows` returns the seeded Brookside Meadows project payload.

A `404` on the backend root `/` is not necessarily a failure. The backend does not serve a page at `/`. If `/health` and the `/api/v1` routes respond, the backend is working as expected. Check `/health` and an `/api/v1` route before concluding the backend is down.

### Backend environment variables

Set these as service variables on the backend service. Local defaults work without them; a deployment sets the ones it needs.

```
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FRONTEND_ORIGIN=https://your-frontend-service.up.railway.app
CAD_UPLOAD_DIR=./cad_uploads
MAX_CAD_UPLOAD_BYTES=5000000
DEMO_MODE=true
```

Notes:

- `FRONTEND_ORIGIN` is the deployed frontend URL. When set, it is added to the allowed CORS origins, so the backend accepts browser calls from the frontend service. This is the only CORS value a deployment usually needs to set.
- `CORS_ORIGINS` is a comma separated list. The deployed frontend origin can be added here as well, but setting `FRONTEND_ORIGIN` is enough.
- `MAX_CAD_UPLOAD_BYTES` sets the DXF upload size limit. `CAD_MAX_UPLOAD_BYTES` is accepted as an alias for the same value.
- `CAD_UPLOAD_DIR` is where uploaded DXF files are stored. See the storage note below.
- `DEMO_MODE` keeps the deployment self-contained with seeded demo data and no authentication.

## Service 2: Next.js frontend

### Source and root directory

- Source: this repository.
- Root directory setting: the repository root.

Railway builds the frontend from the root, where `package.json` and `railway.json` live. The root `railway.json` sets the build and start commands.

### Build command

The build command runs the existing Next.js production build:

```
npm ci && npm run build
```

### Start command

The start command runs the existing Next.js production server bound to the Railway port:

```
npm run start -- --hostname 0.0.0.0 --port $PORT
```

`$PORT` is provided by Railway at runtime. This same command is set in the root `railway.json`.

### Frontend environment variables

Set this as a service variable on the frontend service:

```
NEXT_PUBLIC_API_BASE_URL=https://your-backend-service.up.railway.app
```

Notes:

- `NEXT_PUBLIC_API_BASE_URL` is the public origin of the backend service only, with no trailing slash and no `/api` or `/api/v1` path. The frontend API modules append `/api/v1/...` paths themselves, so adding it here would produce a double prefix and break every call. For example, set `NEXT_PUBLIC_API_BASE_URL=https://your-backend-service.up.railway.app`, not `.../api/v1`.
- This variable is read at build and run time. If the backend URL changes, redeploy the frontend so the new value is built in.
- Locally the default is `http://localhost:8000`, so the frontend works in development without setting anything.

### Frontend redeploy and stale builds

The frontend is a Next.js build. The page content and navigation a visitor sees come from whatever commit Railway last built, not automatically from the latest `main`. Keep these points in mind:

- The live frontend must be redeployed after `NEXT_PUBLIC_API_BASE_URL` changes. The value is compiled into the build, so a changed backend URL only takes effect after a new frontend deploy.
- The frontend build can appear stale if Railway does not redeploy from the latest `main`. If the live homepage or navigation does not match the current `main` branch, trigger a fresh deploy of the frontend service from the latest commit.
- `NEXT_PUBLIC_API_BASE_URL` must be the backend origin only. Do not include `/api/v1` in `NEXT_PUBLIC_API_BASE_URL`; the frontend API modules append `/api/v1/...` paths themselves.

After redeploying, confirm the live site against the checklist in [LIVE_SITE_VERIFICATION.md](LIVE_SITE_VERIFICATION.md).

## API base URL and CORS together

The two services connect through two settings that mirror each other:

- The frontend `NEXT_PUBLIC_API_BASE_URL` points at the backend public URL.
- The backend `FRONTEND_ORIGIN` points at the frontend public URL.

When both are set to the deployed URLs, the frontend can call the backend and the backend allows the browser origin. A visible backend connection banner on the frontend home page reports whether the backend is reachable, so a misconfiguration is easy to spot.

## Known limitations

- This is a demo deployment with no authentication and no role-based access. Every visitor sees the same Brookside Meadows demo data.
- The backend uses SQLite on the service file system. The database is recreated from seed data on each deploy. It is not a managed database and has no migrations.
- Uploaded DXF files are stored under `CAD_UPLOAD_DIR` on the backend service file system. This is demo-local storage and is not persistent across redeploys. To keep uploads, mount a Railway volume at the upload directory path and point `CAD_UPLOAD_DIR` at it.
- Live AI calls are disabled by default. The deterministic mock provider is used, so no API key is required.

## Durable file storage (Production Foundations Sprint 6)

Project document uploads are managed through a storage provider abstraction with two options.

### Local storage (default, development only)

With `STORAGE_PROVIDER=local` (the default), uploaded project files are stored under `LOCAL_STORAGE_DIR` (default `./project_uploads`) on the backend service file system. This is simple for development but is not durable across redeploys without a mounted volume. To keep local uploads on Railway, mount a Railway volume and point `LOCAL_STORAGE_DIR` at it. Even so, object storage is recommended for deployment.

### S3-compatible object storage (recommended for deployment)

Set `STORAGE_PROVIDER=s3` and configure an S3-compatible bucket so uploads survive redeploys. Required and optional backend variables:

- `OBJECT_STORAGE_BUCKET` (required): the bucket name.
- `OBJECT_STORAGE_ACCESS_KEY_ID` and `OBJECT_STORAGE_SECRET_ACCESS_KEY` (required): backend-only credentials.
- `OBJECT_STORAGE_ENDPOINT_URL` (optional): for non-AWS S3-compatible providers (for example MinIO or other providers); leave empty for AWS S3.
- `OBJECT_STORAGE_REGION` (default `us-east-1`).
- `OBJECT_STORAGE_FORCE_PATH_STYLE` (default `true`): path-style addressing for S3-compatible providers.
- `OBJECT_STORAGE_PUBLIC_BASE_URL` (optional) and `OBJECT_STORAGE_SIGNED_URL_EXPIRE_SECONDS` (default `300`).

Object storage credentials are read only when `STORAGE_PROVIDER=s3`. They are backend service variables only. Never put storage credentials in the frontend or in any `NEXT_PUBLIC_*` variable. The frontend downloads files through the access-controlled backend route and never holds storage credentials.

## Demo data note

The backend seeds the Brookside Meadows fixture on startup: documents, a stormwater checklist, findings, plan sheets, CAD-aware metadata, a review packet, a workflow board, a draft response package, a parsed sample DXF, a review cycle, and an initial command center snapshot. This makes the deployed demo immediately explorable without any manual setup.

## No authentication note

This deployment intentionally adds no authentication, no login, and no user accounts. It is a public portfolio demo. Do not put real or sensitive submissions into it.
