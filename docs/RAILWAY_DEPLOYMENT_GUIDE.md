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

- `NEXT_PUBLIC_API_BASE_URL` is the backend origin only. It has no trailing slash and no path. Do not include `/api/v1` (or any `/api` path) in it. The frontend appends `/api/v1/...` to the base URL itself, so a base URL that already includes `/api/v1` produces a wrong `/api/v1/api/v1/...` path and the calls fail.
- Correct: `https://your-backend-service.up.railway.app`
- Wrong: `https://your-backend-service.up.railway.app/api/v1`
- This variable is read at build and run time. If the backend URL changes, redeploy the frontend so the new value is built in.
- Locally the default is `http://localhost:8000`, so the frontend works in development without setting anything.

## API base URL and CORS together

The two services connect through two settings that mirror each other:

- The frontend `NEXT_PUBLIC_API_BASE_URL` points at the backend public origin (no `/api/v1`).
- The backend `FRONTEND_ORIGIN` points at the frontend public URL.

When both are set to the deployed URLs, the frontend can call the backend and the backend allows the browser origin. A visible backend connection banner on the frontend home page reports whether the backend is reachable and distinguishes a missing URL, an unreachable backend, and a base URL that wrongly includes an API path, so a misconfiguration is easy to spot.

## Verifying the backend is live

After the backend service deploys, confirm it is serving the API by opening these URLs in a browser (replace the host with the deployed backend URL):

- `/health` returns a small JSON payload with `status`, `service`, `version`, and `demo_mode`. This is the healthcheck.
- `/api/v1/projects/proj_brookside_meadows` returns the seeded Brookside Meadows project, which confirms the API routes and the seeded demo data are live.

A `404` on the backend root `/` is expected and is not a failure. The backend does not define a route at `/`; it serves the API under `/api/v1` and the healthcheck at `/health`. As long as `/health` and the `/api/v1` routes respond, the backend is healthy. Use `/health` (not `/`) as the Railway healthcheck path.

## Known limitations

- This is a demo deployment with no authentication and no role-based access. Every visitor sees the same Brookside Meadows demo data.
- The backend uses SQLite on the service file system. The database is recreated from seed data on each deploy. It is not a managed database and has no migrations.
- Uploaded DXF files are stored under `CAD_UPLOAD_DIR` on the backend service file system. This is demo-local storage and is not persistent across redeploys. To keep uploads, mount a Railway volume at the upload directory path and point `CAD_UPLOAD_DIR` at it. There is no external object storage.
- Live AI calls are disabled by default. The deterministic mock provider is used, so no API key is required.

## Demo data note

The backend seeds the Brookside Meadows fixture on startup: documents, a stormwater checklist, findings, plan sheets, CAD-aware metadata, a review packet, a workflow board, a draft response package, a parsed sample DXF, a review cycle, and an initial command center snapshot. This makes the deployed demo immediately explorable without any manual setup.

## No authentication note

This deployment intentionally adds no authentication, no login, and no user accounts. It is a public portfolio demo. Do not put real or sensitive submissions into it.
