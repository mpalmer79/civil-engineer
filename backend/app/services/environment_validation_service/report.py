"""Aggregation and public diagnostic reports.

Rolls the individual validation items into a full summary, a sanitized public
readiness summary, storage diagnostics, frontend integration hints, and a static
professional-boundary summary. Every result is a safe operational status. No
secret values, database URL, or raw paths are included. These reports never
approve a project, certify compliance, verify CAD, validate design, declare
safety, resolve an issue, or close an issue.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS

from app.services.environment_validation_service.config import (
    _application_items,
    _authentication_items,
    _cors_items,
    _frontend_integration_items,
    _public_demo_items,
)
from app.services.environment_validation_service.database import _database_items
from app.services.environment_validation_service.errors import _INSECURE_AUTH_SECRET
from app.services.environment_validation_service.storage import (
    _object_storage_items,
    _storage_items,
)


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
