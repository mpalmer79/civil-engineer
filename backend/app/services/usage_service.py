"""Internal usage metering (Production Phase 4B/4C/4D).

Records counts of review-support actions per organization, summarizes usage
against the organization's plan, and (Phase 4D) optionally enforces hard limits
for selected low-risk categories. Enforcement is off by default
(USAGE_ENFORCEMENT_ENABLED), so existing behavior, local development, and tests
are never blocked, and the public Brookside demo and the demo organization are
never enforced.

No usage record carries file content, document text, or any secret. Usage is
never sent to any external service.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.safety import ALLOWED_USAGE_CATEGORIES
from app.db import models
from app.services import billing_service

# Fraction of a limit at which usage is reported as "approaching".
_APPROACHING_FRACTION = 0.8

# The demo organization is excluded from usage metering so seeded demo activity
# never counts against any plan or pollutes usage summaries.
_EXCLUDED_ORG_IDS = {"org_internal_demo"}

# Categories that are hard-enforced when USAGE_ENFORCEMENT_ENABLED is true. These
# are single-mutation, organization-scoped, user-driven actions where a clean
# pre-check cannot leave partial state. Other categories stay advisory: AI calls
# (no live AI), pages indexed and CAD parses (counted inside internal/seed
# flows), the public pilot request, and the public demo. See
# docs/BILLING_AND_USAGE.md.
ENFORCED_CATEGORIES = {
    "project_created",
    "document_uploaded",
    "review_packet_generated",
}


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


def usage_summary(
    db: Session, organization_id: str, settings: Settings | None = None
) -> dict[str, Any]:
    """Return a usage summary for an organization against its plan limits.

    Each metered limit reports the category, used count, limit, an advisory
    status (ok, approaching, over), and whether it is hard-enforced. The
    top-level enforcement is "enforced" when enforcement is enabled, else
    "advisory".
    """

    settings = settings or get_settings()
    enforcing = bool(settings.USAGE_ENFORCEMENT_ENABLED)
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
                "enforced": enforcing and category in ENFORCED_CATEGORIES,
            }
        )
    return {
        "organization_id": organization_id,
        "plan_code": sub.plan_code,
        "plan_name": plan["name"],
        "subscription_status": sub.status,
        "enforcement": "enforced" if enforcing else "advisory",
        "limits": limits,
        "totals": totals,
    }


def check_limit(
    db: Session,
    *,
    category: str,
    organization_id: str | None,
    settings: Settings | None = None,
) -> None:
    """Raise 402 limit_exceeded when an enforced category is at or over its limit.

    A no-op unless USAGE_ENFORCEMENT_ENABLED is true and the category is in
    ENFORCED_CATEGORIES. The demo organization and a null organization (public
    demo or global actions) are never enforced, so the public Brookside demo is
    never blocked. This must be called before any mutation so a blocked action
    leaves no partial state.
    """

    settings = settings or get_settings()
    if not settings.USAGE_ENFORCEMENT_ENABLED:
        return
    if category not in ENFORCED_CATEGORIES:
        return
    if not organization_id or organization_id in _EXCLUDED_ORG_IDS:
        return
    sub = billing_service.get_or_create_subscription(db, organization_id)
    plan = billing_service.get_plan(sub.plan_code)
    # Find the plan limit key for this category.
    limit_key = next(
        (k for k, c in billing_service.LIMIT_TO_CATEGORY.items() if c == category),
        None,
    )
    if limit_key is None:
        return
    limit = plan["limits"].get(limit_key)
    if limit is None:
        return
    used = usage_totals(db, organization_id).get(category, 0)
    if used >= limit:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "limit_exceeded",
                "category": category,
                "limit": limit,
                "used": used,
                "plan_code": sub.plan_code,
                "message": (
                    f"Plan limit reached for {limit_key} "
                    f"({used}/{limit}). Upgrade the plan to continue."
                ),
            },
        )
