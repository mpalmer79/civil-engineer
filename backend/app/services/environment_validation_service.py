"""Environment validation and deployment diagnostics (Sprint 10).

Civil Engineer AI validates critical environment configuration so an operator can
confirm a deployment is wired correctly before relying on it. Every result is a
safe operational status. This service never returns secret values: it reports
whether a setting is configured, never what it is. Database URLs, the auth secret,
object storage credentials, tokens, and raw file system paths are never included
in any response.

These checks describe configuration and connectivity readiness only. They do not
approve a project, certify compliance, verify CAD, validate design, declare
safety, resolve an issue, or close an issue.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.safety import (
    ALLOWED_DIAGNOSTIC_CATEGORIES,
    ALLOWED_DIAGNOSTIC_SEVERITIES,
    ALLOWED_DIAGNOSTIC_STATUSES,
    PROHIBITED_FINAL_DECISION_WORDS,
)

# The built-in development-only auth secret. A deployment that still uses it is
# flagged for operator review; the value itself is never returned.
_INSECURE_AUTH_SECRET = "dev-only-insecure-change-me"


def _item(
    *,
    category: str,
    key: str,
    status: str,
    severity: str,
    message: str,
    required: bool,
    configured: bool,
    public_hint: str | None = None,
    remediation_hint: str | None = None,
) -> dict[str, Any]:
    """Build a validation item, asserting safe category/status/severity values."""

    assert category in ALLOWED_DIAGNOSTIC_CATEGORIES, category
    assert status in ALLOWED_DIAGNOSTIC_STATUSES, status
    assert severity in ALLOWED_DIAGNOSTIC_SEVERITIES, severity
    return {
        "category": category,
        "key": key,
        "status": status,
        "severity": severity,
        "message": message,
        "required": required,
        "configured": configured,
        "public_hint": public_hint,
        "remediation_hint": remediation_hint,
    }


def _bool_hint(value: bool) -> str:
    return "enabled" if value else "disabled"


def _application_items(settings: Settings) -> list[dict[str, Any]]:
    return [
        _item(
            category="application",
            key="APP_VERSION",
            status="ready",
            severity="info",
            message="Application version is set.",
            required=True,
            configured=bool(settings.APP_VERSION),
            public_hint=settings.APP_VERSION,
        ),
        _item(
            category="application",
            key="API_V1_PREFIX",
            status="configured",
            severity="info",
            message="API version prefix is configured.",
            required=True,
            configured=bool(settings.API_V1_PREFIX),
            public_hint=settings.API_V1_PREFIX,
        ),
    ]


def _database_items(settings: Settings) -> list[dict[str, Any]]:
    from app.db.database import database_provider

    configured = bool(settings.DATABASE_URL)
    provider = database_provider(settings.DATABASE_URL)
    is_sqlite = provider == "sqlite"
    # The provider class is a safe operational hint derived from the URL scheme
    # only; the URL itself is never returned. SQLite on a deployment without a
    # mounted volume is ephemeral, and in strict production mode it is not
    # supported at all, so it is surfaced for operator review.
    if not configured:
        return [
            _item(
                category="database",
                key="DATABASE_URL",
                status="missing_required",
                severity="critical",
                message="Database connection is not configured.",
                required=True,
                configured=False,
                remediation_hint=(
                    "Set DATABASE_URL on the backend service to a database "
                    "connection string."
                ),
            )
        ]
    if is_sqlite:
        if settings.is_production:
            return [
                _item(
                    category="database",
                    key="DATABASE_URL",
                    status="missing_required",
                    severity="critical",
                    message=(
                        "SQLite is configured but APP_ENV is production. "
                        "Production SaaS requires a Postgres database."
                    ),
                    required=True,
                    configured=True,
                    public_hint="sqlite",
                    remediation_hint=(
                        "Set DATABASE_URL to a Postgres connection string for "
                        "production, or set APP_ENV to development or pilot for "
                        "prototype use."
                    ),
                )
            ]
        return [
            _item(
                category="database",
                key="DATABASE_URL",
                status="warning",
                severity="warning",
                message=(
                    "A local SQLite database is configured. It is supported for "
                    "local development, tests, and the pilot prototype. On a "
                    "deployment without a mounted volume it is recreated from "
                    "seed data on each redeploy."
                ),
                required=True,
                configured=True,
                public_hint="sqlite",
                remediation_hint=(
                    "For production SaaS, set DATABASE_URL to a Postgres "
                    "connection string and run 'alembic upgrade head'."
                ),
            )
        ]
    return [
        _item(
            category="database",
            key="DATABASE_URL",
            status="configured",
            severity="info",
            message=(
                "A Postgres database connection is configured."
                if provider == "postgres"
                else "An external database connection is configured."
            ),
            required=True,
            configured=True,
            public_hint=provider if provider == "postgres" else "external",
        )
    ]


def _authentication_items(settings: Settings) -> list[dict[str, Any]]:
    secret_set = bool(settings.AUTH_SECRET_KEY)
    secret_is_default = settings.AUTH_SECRET_KEY == _INSECURE_AUTH_SECRET
    if not secret_set:
        secret_item = _item(
            category="authentication",
            key="AUTH_SECRET_KEY",
            status="missing_required",
            severity="critical",
            message="The auth token signing secret is not set.",
            required=True,
            configured=False,
            remediation_hint=(
                "Set AUTH_SECRET_KEY on the backend service to a long random "
                "secret. Never expose it to the frontend."
            ),
        )
    elif secret_is_default:
        secret_item = _item(
            category="authentication",
            key="AUTH_SECRET_KEY",
            status="needs_operator_review",
            severity="warning",
            message=(
                "The auth signing secret is still the development-only default."
            ),
            required=True,
            configured=True,
            remediation_hint=(
                "Override AUTH_SECRET_KEY with a strong unique secret before any "
                "real use. The value is never returned by this API."
            ),
        )
    else:
        secret_item = _item(
            category="authentication",
            key="AUTH_SECRET_KEY",
            status="configured",
            severity="info",
            message="A custom auth signing secret is configured.",
            required=True,
            configured=True,
        )
    return [
        secret_item,
        _item(
            category="authentication",
            key="AUTH_TOKEN_EXPIRE_MINUTES",
            status="configured",
            severity="info",
            message="Access token lifetime is configured.",
            required=False,
            configured=True,
            public_hint=str(settings.AUTH_TOKEN_EXPIRE_MINUTES),
        ),
        _item(
            category="authentication",
            key="AUTH_DEMO_MODE",
            status="configured" if settings.AUTH_DEMO_MODE else "disabled",
            severity="info",
            message=f"Auth demo mode is {_bool_hint(settings.AUTH_DEMO_MODE)}.",
            required=False,
            configured=True,
            public_hint=_bool_hint(settings.AUTH_DEMO_MODE),
        ),
        _item(
            category="authentication",
            key="AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS",
            status="configured",
            severity="info",
            message=(
                "Login requirement for real project actions is "
                f"{_bool_hint(settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS)}."
            ),
            required=False,
            configured=True,
            public_hint=_bool_hint(
                settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
            ),
        ),
    ]


def _public_demo_items(settings: Settings) -> list[dict[str, Any]]:
    return [
        _item(
            category="public_demo",
            key="AUTH_ALLOW_PUBLIC_DEMO",
            status="configured" if settings.AUTH_ALLOW_PUBLIC_DEMO else "disabled",
            severity="info",
            message=(
                "Reading the public Brookside Meadows demo without a login is "
                f"{_bool_hint(settings.AUTH_ALLOW_PUBLIC_DEMO)}."
            ),
            required=False,
            configured=True,
            public_hint=_bool_hint(settings.AUTH_ALLOW_PUBLIC_DEMO),
        ),
        _item(
            category="public_demo",
            key="AUTH_SEED_DEMO_USERS",
            status="configured" if settings.AUTH_SEED_DEMO_USERS else "disabled",
            severity="notice" if settings.AUTH_SEED_DEMO_USERS else "info",
            message=(
                "Seeded local demo users are "
                f"{_bool_hint(settings.AUTH_SEED_DEMO_USERS)}."
            ),
            required=False,
            configured=True,
            public_hint=_bool_hint(settings.AUTH_SEED_DEMO_USERS),
            remediation_hint=(
                "Set AUTH_SEED_DEMO_USERS=false to disable the seeded demo "
                "accounts before any real use."
                if settings.AUTH_SEED_DEMO_USERS
                else None
            ),
        ),
    ]


def _storage_items(settings: Settings) -> list[dict[str, Any]]:
    provider = (settings.STORAGE_PROVIDER or "local").strip().lower()
    items = [
        _item(
            category="storage",
            key="STORAGE_PROVIDER",
            status="configured",
            severity="info",
            message=f"Storage provider '{provider}' is selected.",
            required=True,
            configured=True,
            public_hint=provider,
        )
    ]
    # LOCAL_STORAGE_DIR is reported as configured only. The raw path is never
    # exposed in diagnostics, so public_hint stays None.
    items.append(
        _item(
            category="storage",
            key="LOCAL_STORAGE_DIR",
            status="configured" if provider == "local" else "disabled",
            severity=(
                "warning"
                if provider == "local"
                else "info"
            ),
            message=(
                "Local development storage is selected. On a deployment without "
                "a mounted volume, uploaded files are not durable across "
                "redeploys."
                if provider == "local"
                else "Local storage is not the selected provider."
            ),
            required=False,
            configured=True,
            remediation_hint=(
                "For durable deployment storage, set STORAGE_PROVIDER=s3 and the "
                "object storage settings, or mount a persistent volume."
                if provider == "local"
                else None
            ),
        )
    )
    return items


def _object_storage_items(settings: Settings) -> list[dict[str, Any]]:
    provider = (settings.STORAGE_PROVIDER or "local").strip().lower()
    if provider != "s3":
        return [
            _item(
                category="object_storage",
                key="OBJECT_STORAGE",
                status="disabled",
                severity="info",
                message="Object storage is not the selected provider.",
                required=False,
                configured=False,
                public_hint="not_selected",
            )
        ]
    # Provider is s3. Report only whether each setting is configured, never the
    # value. Credentials are confirmed present or missing; they are never echoed.
    bucket_set = bool(settings.OBJECT_STORAGE_BUCKET)
    access_key_set = bool(settings.OBJECT_STORAGE_ACCESS_KEY_ID)
    secret_set = bool(settings.OBJECT_STORAGE_SECRET_ACCESS_KEY)
    missing = not (bucket_set and access_key_set and secret_set)
    items = [
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_BUCKET",
            status="configured" if bucket_set else "missing_required",
            severity="info" if bucket_set else "critical",
            message=(
                "Object storage bucket is configured."
                if bucket_set
                else "Object storage bucket is not configured."
            ),
            required=True,
            configured=bucket_set,
            remediation_hint=(
                None
                if bucket_set
                else "Set OBJECT_STORAGE_BUCKET on the backend service."
            ),
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_REGION",
            status="configured",
            severity="info",
            message="Object storage region is configured.",
            required=False,
            configured=bool(settings.OBJECT_STORAGE_REGION),
            public_hint=settings.OBJECT_STORAGE_REGION or None,
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_ENDPOINT_URL",
            status="configured" if settings.OBJECT_STORAGE_ENDPOINT_URL else "missing_optional",
            severity="info",
            message=(
                "A custom object storage endpoint is configured."
                if settings.OBJECT_STORAGE_ENDPOINT_URL
                else "Using the default AWS S3 endpoint (no custom endpoint set)."
            ),
            required=False,
            configured=bool(settings.OBJECT_STORAGE_ENDPOINT_URL),
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_ACCESS_KEY_ID",
            status="configured" if access_key_set else "missing_required",
            severity="info" if access_key_set else "critical",
            message=(
                "Object storage access key is configured."
                if access_key_set
                else "Object storage access key is not configured."
            ),
            required=True,
            configured=access_key_set,
            remediation_hint=(
                None
                if access_key_set
                else "Set OBJECT_STORAGE_ACCESS_KEY_ID on the backend service only."
            ),
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_SECRET_ACCESS_KEY",
            status="configured" if secret_set else "missing_required",
            severity="info" if secret_set else "critical",
            message=(
                "Object storage secret access key is configured."
                if secret_set
                else "Object storage secret access key is not configured."
            ),
            required=True,
            configured=secret_set,
            remediation_hint=(
                None
                if secret_set
                else "Set OBJECT_STORAGE_SECRET_ACCESS_KEY on the backend service only."
            ),
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_SIGNED_URL_EXPIRE_SECONDS",
            status="configured",
            severity="info",
            message="Signed URL expiry is configured.",
            required=False,
            configured=True,
            public_hint=str(settings.OBJECT_STORAGE_SIGNED_URL_EXPIRE_SECONDS),
        ),
    ]
    if missing:
        items.append(
            _item(
                category="object_storage",
                key="OBJECT_STORAGE",
                status="needs_operator_review",
                severity="critical",
                message=(
                    "Object storage is selected but one or more required "
                    "settings are missing."
                ),
                required=True,
                configured=False,
                remediation_hint=(
                    "Set the bucket, access key, and secret access key on the "
                    "backend service only."
                ),
            )
        )
    return items


def _cors_items(settings: Settings) -> list[dict[str, Any]]:
    frontend_origin_set = bool(settings.FRONTEND_ORIGIN.strip())
    origin_count = len(settings.cors_origins_list)
    return [
        _item(
            category="cors",
            key="FRONTEND_ORIGIN",
            status="configured" if frontend_origin_set else "missing_optional",
            severity="info" if frontend_origin_set else "notice",
            message=(
                "The deployed frontend origin is configured for CORS."
                if frontend_origin_set
                else "No deployed frontend origin is set; only local dev origins "
                "are allowed."
            ),
            required=False,
            configured=frontend_origin_set,
            remediation_hint=(
                None
                if frontend_origin_set
                else "Set FRONTEND_ORIGIN to the deployed frontend URL so the "
                "browser may call the backend."
            ),
        ),
        _item(
            category="cors",
            key="CORS_ORIGINS",
            status="configured",
            severity="info",
            message=f"{origin_count} allowed browser origin(s) are configured.",
            required=False,
            configured=origin_count > 0,
            public_hint=str(origin_count),
        ),
    ]


def _frontend_integration_items(settings: Settings) -> list[dict[str, Any]]:
    return [
        _item(
            category="frontend_integration",
            key="NEXT_PUBLIC_API_BASE_URL",
            status="needs_operator_review",
            severity="notice",
            message=(
                "The frontend NEXT_PUBLIC_API_BASE_URL must be the backend "
                "origin only, with no /api/v1 path. It is a frontend variable, "
                "set on the frontend service, and is not read by the backend."
            ),
            required=False,
            configured=False,
            public_hint=settings.API_V1_PREFIX,
            remediation_hint=(
                "Set NEXT_PUBLIC_API_BASE_URL to the backend public origin and "
                "redeploy the frontend after changing it. Never put backend "
                "secrets in any NEXT_PUBLIC_ variable."
            ),
        )
    ]


def validate_environment(settings: Settings | None = None) -> dict[str, Any]:
    """Return the full environment validation summary with safe statuses only."""

    settings = settings or get_settings()
    items: list[dict[str, Any]] = []
    items += _application_items(settings)
    items += _database_items(settings)
    items += _authentication_items(settings)
    items += _public_demo_items(settings)
    items += _storage_items(settings)
    items += _object_storage_items(settings)
    items += _cors_items(settings)
    items += _frontend_integration_items(settings)

    counts: dict[str, int] = {}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1

    overall = _overall_status(items)
    return {
        "overall_status": overall,
        "item_count": len(items),
        "status_counts": counts,
        "items": items,
    }


def _overall_status(items: list[dict[str, Any]]) -> str:
    """Roll item statuses up into a single safe operational status."""

    statuses = {item["status"] for item in items}
    if "missing_required" in statuses:
        return "needs_operator_review"
    if "needs_operator_review" in statuses:
        return "needs_operator_review"
    if "warning" in statuses:
        return "warning"
    return "ready"


def get_readiness(
    db: Session, settings: Settings | None = None
) -> dict[str, Any]:
    """Return a public, sanitized readiness summary.

    Checks database connectivity, the presence of required configuration, and
    storage provider readiness at a lightweight level. No secret values, no
    database URL, and no raw paths are included.
    """

    settings = settings or get_settings()
    checks: list[dict[str, Any]] = []

    # Database connectivity: run a trivial query. Never report the URL. The
    # provider class (sqlite/postgres/other) is a safe operational hint derived
    # from the URL scheme only; no host, credential, or path is read.
    from app.db.database import database_provider

    db_provider = database_provider(settings.DATABASE_URL)
    try:
        db.execute(text("SELECT 1"))
        checks.append(
            {
                "category": "database",
                "status": "ready",
                "message": (
                    f"Database connection responded (provider: {db_provider})."
                ),
            }
        )
    except Exception:  # noqa: BLE001 - connectivity failure is reported safely
        checks.append(
            {
                "category": "database",
                "status": "unavailable",
                "message": (
                    f"Database connection did not respond "
                    f"(provider: {db_provider})."
                ),
            }
        )

    # Migration status: whether the schema is under Alembic control and current.
    # Reported revisions are short Alembic hashes, never connection details.
    from app.db.migration_status import get_migration_status

    migration = get_migration_status(db)
    migration_check_status = (
        "ready" if migration["status"] in {"up_to_date", "managed"} else "warning"
    )
    checks.append(
        {
            "category": "migrations",
            "status": migration_check_status,
            "message": migration["message"],
        }
    )

    # Required configuration presence.
    if settings.AUTH_SECRET_KEY:
        auth_status = (
            "needs_operator_review"
            if settings.AUTH_SECRET_KEY == _INSECURE_AUTH_SECRET
            else "configured"
        )
        auth_message = (
            "The auth signing secret is the development-only default."
            if auth_status == "needs_operator_review"
            else "The auth signing secret is configured."
        )
    else:
        auth_status = "missing_required"
        auth_message = "The auth signing secret is not set."
    checks.append(
        {
            "category": "authentication",
            "status": auth_status,
            "message": auth_message,
        }
    )

    # Storage provider readiness at a lightweight level (no credentials).
    from app.services.storage import storage_service

    storage_info = storage_service.storage_health()
    provider = storage_info.get("provider", "unknown")
    storage_configured = bool(storage_info.get("configured"))
    checks.append(
        {
            "category": "storage",
            "status": "ready" if storage_configured else "warning",
            "message": (
                f"Storage provider '{provider}' is configured."
                if storage_configured
                else f"Storage provider '{provider}' needs configuration review."
            ),
        }
    )

    overall = _readiness_overall(checks)
    return {
        "status": overall,
        "service": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "demo_mode": settings.DEMO_MODE,
        # Safe operational context. app_env and the database provider class carry
        # no secret; migration_status reports control state and short revision
        # hashes only. None of these expose a URL, host, credential, or path.
        "app_env": settings.app_env,
        "database_provider": db_provider,
        "migration_status": migration["status"],
        "checks": checks,
    }


def _readiness_overall(checks: list[dict[str, Any]]) -> str:
    statuses = {check["status"] for check in checks}
    if "unavailable" in statuses or "missing_required" in statuses:
        return "needs_operator_review"
    if "needs_operator_review" in statuses or "warning" in statuses:
        return "warning"
    return "ready"


def get_storage_diagnostics(settings: Settings | None = None) -> dict[str, Any]:
    """Return safe storage provider diagnostics with no credentials or paths."""

    settings = settings or get_settings()
    from app.services.storage import storage_service

    info = storage_service.storage_health()
    provider = info.get("provider", "unknown")
    configured = bool(info.get("configured"))
    items = [item for item in _storage_items(settings)]
    items += _object_storage_items(settings)
    return {
        "provider": provider,
        "configured": configured,
        "status": "ready" if configured else "warning",
        "message": (
            "Local development storage is selected. Uploaded files are not "
            "durable across redeploys without a mounted volume."
            if provider == "local"
            else "Object storage configuration was checked."
        ),
        "items": items,
    }


def get_frontend_config_diagnostics(
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Return backend-side frontend integration hints. No secrets."""

    settings = settings or get_settings()
    return {
        "api_prefix": settings.API_V1_PREFIX,
        "expects_backend_origin_only": True,
        "frontend_env_var": "NEXT_PUBLIC_API_BASE_URL",
        "guidance": [
            "NEXT_PUBLIC_API_BASE_URL must be the backend origin only.",
            "Do not include /api/v1 in NEXT_PUBLIC_API_BASE_URL.",
            "Redeploy the frontend after changing NEXT_PUBLIC_API_BASE_URL.",
            "Never put backend secrets in any NEXT_PUBLIC_ variable.",
        ],
    }


def get_security_boundary_diagnostics() -> dict[str, Any]:
    """Return a static professional-boundary summary for UI self-checks."""

    return {
        "summary": (
            "Civil Engineer AI supports human plan review. It does not approve "
            "plans, certify compliance, verify CAD, validate design, declare a "
            "project safe, make final engineering decisions, resolve issues, "
            "close issues, or replace a licensed Professional Engineer."
        ),
        "prohibited_outcome_terms": sorted(PROHIBITED_FINAL_DECISION_WORDS),
        "diagnostics_are_operational_only": True,
    }
