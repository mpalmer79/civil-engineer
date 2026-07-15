"""Database configuration validation items.

Reports whether a database connection is configured and its provider class,
derived from the URL scheme only. The database URL itself is never returned.
These checks describe configuration readiness only and never approve a project,
certify compliance, or validate design.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings

from app.services.environment_validation_service._common import _item


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
