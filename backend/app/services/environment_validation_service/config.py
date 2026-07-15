"""Application, authentication, public demo, CORS, and frontend configuration items.

Reports whether each configuration value is set, never the value itself. The
auth signing secret is never returned. These checks describe configuration
readiness only and never approve a project, certify compliance, or validate
design.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings

from app.services.environment_validation_service._common import _bool_hint, _item
from app.services.environment_validation_service.errors import _INSECURE_AUTH_SECRET


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
