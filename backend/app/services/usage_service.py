"""Internal usage metering (Production Phase 4B/4C).

Records counts of review-support actions per organization for advisory usage
limits, and summarizes usage against the organization's plan. Usage is advisory
in this phase: it is tracked and surfaced with warning states, but actions are
not hard-blocked, so existing behavior and the public demo are never interrupted.

No usage record carries file content, document text, or any secret. Usage is
never sent to any external service.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.safety import ALLOWED_USAGE_CATEGORIES
from app.db import models
from app.services import billing_service

# Fraction of a limit at which usage is reported as "approaching".
_APPROACHING_FRACTION = 0.8

# The demo organization is excluded from usage metering so seeded demo activity
# never counts against any plan or pollutes usage summaries.
_EXCLUDED_ORG_IDS = {"org_internal_demo"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def record_usage(
    db: Session,
    *,
    category: str,
    organization_id: str | None = None,
    project_id: str | None = None,
    quantity: int = 1,
) -> models.UsageEvent:
    """Record a usage event. Raises ValueError on an unknown category.

    The event is added to the session and flushed, participating in the caller's
    transaction. Callers that must never fail on metering should use
    record_usage_safe instead.
    """

    if category not in ALLOWED_USAGE_CATEGORIES:
        raise ValueError(f"Unknown usage category '{category}'.")
    event = models.UsageEvent(
        usage_event_id=f"use_{_short()}",
        organization_id=organization_id,
        project_id=project_id,
        category=category,
        quantity=max(1, int(quantity)),
        created_at=_now(),
    )
    db.add(event)
    db.flush()
    return event


def record_usage_safe(
    db: Session,
    *,
    category: str,
    organization_id: str | None = None,
    project_id: str | None = None,
    quantity: int = 1,
) -> models.UsageEvent | None:
    """Best-effort usage recording for hooks in user-driven flows.

    Skips the seeded demo organization, and never raises: a metering failure must
    not break the review-support action it accompanies. Returns the event or None.
    """

    if organization_id in _EXCLUDED_ORG_IDS:
        return None
    try:
        return record_usage(
            db,
            category=category,
            organization_id=organization_id,
            project_id=project_id,
            quantity=quantity,
        )
    except Exception:  # noqa: BLE001 - metering must never break the action
        return None


def usage_totals(db: Session, organization_id: str) -> dict[str, int]:
    """Return summed usage quantity per category for an organization."""

    rows = db.execute(
        select(
            models.UsageEvent.category,
            func.coalesce(func.sum(models.UsageEvent.quantity), 0),
        )
        .where(models.UsageEvent.organization_id == organization_id)
        .group_by(models.UsageEvent.category)
    ).all()
    return {category: int(total) for category, total in rows}


def _limit_status(used: int, limit: int | None) -> str:
    """Classify usage against a limit: ok, approaching, or over."""

    if limit is None:
        return "ok"
    if limit <= 0:
        return "over" if used > 0 else "ok"
    if used >= limit:
        return "over"
    if used >= int(limit * _APPROACHING_FRACTION):
        return "approaching"
    return "ok"


def usage_summary(db: Session, organization_id: str) -> dict[str, Any]:
    """Return a usage summary for an organization against its plan limits.

    Each metered limit reports the category, used count, limit, and an advisory
    status (ok, approaching, over). Limits are advisory and do not block actions.
    """

    sub = billing_service.get_or_create_subscription(db, organization_id)
    plan = billing_service.get_plan(sub.plan_code)
    totals = usage_totals(db, organization_id)
    limits: list[dict[str, Any]] = []
    for limit_key, category in billing_service.LIMIT_TO_CATEGORY.items():
        limit = plan["limits"].get(limit_key)
        used = totals.get(category, 0)
        limits.append(
            {
                "key": limit_key,
                "category": category,
                "used": used,
                "limit": limit,
                "status": _limit_status(used, limit),
            }
        )
    return {
        "organization_id": organization_id,
        "plan_code": sub.plan_code,
        "plan_name": plan["name"],
        "subscription_status": sub.status,
        "enforcement": "advisory",
        "limits": limits,
        "totals": totals,
    }
