# API: Health, Readiness, and Diagnostics

This document describes the health, readiness, and diagnostics routes added in
Production Foundations Sprint 10. Every route reports operational status only. No
route returns a secret value, a credential, a raw path, a storage key, or a signed
URL. The detailed diagnostics are access controlled; the readiness and guidance
routes are public but sanitized.

The diagnostics routes live in `backend/app/api/v1/diagnostics.py` and are backed
by `backend/app/services/environment_validation_service.py`.

## GET /health

- Method: GET
- Path: `/health`
- Access: public. No secrets.

Lightweight liveness check. Railway uses it as the healthcheck path.

```json
{
  "status": "ok",
  "service": "civil-engineer-ai",
  "version": "10.0.0",
  "demo_mode": true
}
```

Security note: returns safe runtime metadata only (status, service name, version,
demo mode). No configuration detail and no secrets.

## GET /api/v1/readiness

- Method: GET
- Path: `/api/v1/readiness`
- Access: public, sanitized.

Sanitized readiness summary. Checks database connectivity with a `SELECT 1`,
confirms required configuration is present, and reports storage provider
readiness.

```json
{
  "status": "ready",
  "service": "civil-engineer-ai",
  "version": "10.0.0",
  "demo_mode": true,
  "checks": [
    {
      "category": "database",
      "status": "ready",
      "message": "Database connection responded."
    },
    {
      "category": "authentication",
      "status": "configured",
      "message": "Authentication configuration is present."
    },
    {
      "category": "storage",
      "status": "ready",
      "message": "Storage provider is ready."
    }
  ]
}
```

Security note: each check reports a category, an operational status, and a
message. It never returns a configuration value, a path, or a credential. The
response stays public because it is sanitized to operational status only.

## GET /api/v1/diagnostics/environment

- Method: GET
- Path: `/api/v1/diagnostics/environment`
- Access: requires an organization admin (org_admin).

Detailed environment diagnostic. Reports an operational status per configuration
item with a remediation hint. Never returns a secret value.

```json
{
  "overall_status": "needs_operator_review",
  "item_count": 3,
  "status_counts": {
    "ready": 1,
    "configured": 1,
    "needs_operator_review": 1
  },
  "items": [
    {
      "category": "database",
      "key": "DATABASE_URL",
      "status": "ready",
      "severity": "info",
      "message": "Database configuration is present.",
      "required": true,
      "configured": true,
      "public_hint": "Backend service variable. Never exposed to the frontend.",
      "remediation_hint": "No action needed."
    },
    {
      "category": "authentication",
      "key": "AUTH_SECRET_KEY",
      "status": "needs_operator_review",
      "severity": "warning",
      "message": "Auth secret is set to the development default.",
      "required": true,
      "configured": true,
      "public_hint": "Backend service variable. Value is never returned.",
      "remediation_hint": "Set AUTH_SECRET_KEY to a unique value before real use."
    },
    {
      "category": "storage",
      "key": "STORAGE_PROVIDER",
      "status": "configured",
      "severity": "info",
      "message": "Storage provider is configured.",
      "required": false,
      "configured": true,
      "public_hint": "Backend service variable.",
      "remediation_hint": "No action needed."
    }
  ]
}
```

Security note: requires an organization admin. Items report whether a value is
present and whether it looks ready, never the value itself. Secret-like values are
never returned, and path-like values report only that a path is set.

## GET /api/v1/diagnostics/storage

- Method: GET
- Path: `/api/v1/diagnostics/storage`
- Access: requires an authenticated user.

Storage diagnostic. Reports provider name, configuration presence, and an
operational status. No credentials. Bucket information is limited to configured or
not-configured, and no paths are returned.

```json
{
  "provider": "s3",
  "configured": true,
  "status": "ready",
  "message": "Object storage provider is configured.",
  "items": [
    {
      "category": "object_storage",
      "key": "OBJECT_STORAGE_BUCKET",
      "status": "configured",
      "severity": "info",
      "message": "Bucket is configured.",
      "required": true,
      "configured": true,
      "public_hint": "Backend service variable.",
      "remediation_hint": "No action needed."
    },
    {
      "category": "object_storage",
      "key": "OBJECT_STORAGE_ACCESS_KEY_ID",
      "status": "configured",
      "severity": "info",
      "message": "Access key is configured.",
      "required": true,
      "configured": true,
      "public_hint": "Backend-only credential. Value is never returned.",
      "remediation_hint": "No action needed."
    }
  ]
}
```

Security note: requires an authenticated user. Reports configured or
not-configured only. Never returns bucket values, paths, storage keys, signed
URLs, or object storage credentials.

## GET /api/v1/diagnostics/frontend-config

- Method: GET
- Path: `/api/v1/diagnostics/frontend-config`
- Access: public.

Frontend connection guidance. Explains how the frontend should reach the backend.

```json
{
  "api_prefix": "/api/v1",
  "expects_backend_origin_only": true,
  "frontend_env_var": "NEXT_PUBLIC_API_BASE_URL",
  "guidance": [
    "Set NEXT_PUBLIC_API_BASE_URL to the backend origin only.",
    "Do not include /api/v1 in NEXT_PUBLIC_API_BASE_URL.",
    "The frontend appends /api/v1 itself.",
    "Redeploy the frontend after changing NEXT_PUBLIC_API_BASE_URL."
  ]
}
```

Security note: public guidance only. Returns no configuration values and no
secrets.

## GET /api/v1/diagnostics/security-boundary

- Method: GET
- Path: `/api/v1/diagnostics/security-boundary`
- Access: public.

Security boundary statement. Restates that diagnostics are operational indicators
only.

```json
{
  "summary": "Diagnostics report deployment operational status only.",
  "prohibited_outcome_terms": [
    "approved",
    "certified",
    "compliant",
    "verified",
    "validated",
    "safe"
  ],
  "diagnostics_are_operational_only": true
}
```

Security note: public statement only. The listed terms are surfaced to make
explicit that diagnostics never produce an engineering or compliance outcome.

## Allowed vocabularies

Diagnostics use a fixed vocabulary so callers can rely on stable values.

### Status values

- `ready`
- `configured`
- `missing_required`
- `missing_optional`
- `warning`
- `disabled`
- `unavailable`
- `needs_operator_review`

### Categories

- `application`
- `database`
- `authentication`
- `storage`
- `object_storage`
- `public_demo`
- `cors`
- `deployment`
- `frontend_integration`

### Severities

- `info`
- `notice`
- `warning`
- `critical`

These status values are operational indicators only. None of them represents an
approval, a certification, a compliance determination, or an engineering outcome.
