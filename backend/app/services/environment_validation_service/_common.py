"""Shared helpers for environment validation.

Builds individual validation items with safe category, status, and severity
values. These checks describe configuration and connectivity readiness only.
They never approve a project, certify compliance, verify CAD, validate design,
declare safety, resolve an issue, or close an issue. This service never returns
secret values: it reports whether a setting is configured, never what it is.
"""

from __future__ import annotations

from typing import Any

from app.core.safety import (
    ALLOWED_DIAGNOSTIC_CATEGORIES,
    ALLOWED_DIAGNOSTIC_SEVERITIES,
    ALLOWED_DIAGNOSTIC_STATUSES,
)


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
