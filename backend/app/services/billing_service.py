"""Billing and subscription foundation (Production Phase 4B/4C).

Billing is deferred in this phase. This module provides the billing-readiness
foundation: a code-defined set of subscription plans with advisory usage limits,
and per-organization subscription posture. Live Stripe checkout and webhooks are
not wired; the API and UI report an honest inactive state until a Stripe secret
key is configured (see config.billing_enabled). No real payment is processed.

A plan or subscription state is an account-posture label only. It never implies a
review outcome, approval, certification, or compliance, and it never changes the
review-support boundary.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import models

# Plan limit keys map to the cumulative usage categories they bound. A value of
# None means the limit is not metered for that plan (advisory unlimited). These
# limits are advisory in this phase: usage is tracked and surfaced, but actions
# are not hard-blocked. See docs/BILLING_AND_USAGE.md.
LIMIT_TO_CATEGORY: dict[str, str] = {
    "projects": "project_created",
    "documents": "document_uploaded",
    "pdf_pages": "pages_indexed",
    "cad_files": "cad_parsed",
    "review_packets": "review_packet_generated",
    "ai_calls": "ai_call_attempted",
}

# Canonical plan definitions. Prices are intentionally not asserted as active
# charges: billing is inactive in this phase, so price_display is descriptive
# only and the UI shows an honest inactive state.
PLAN_DEFINITIONS: dict[str, dict[str, Any]] = {
    "demo": {
        "plan_code": "demo",
        "name": "Demo",
        "description": (
            "Public Brookside Meadows demo and evaluation. No login required for "
            "the public demo surfaces."
        ),
        "price_display": "Free",
        "sort_order": 0,
        "limits": {
            "projects": 1,
            "documents": 5,
            "pdf_pages": 100,
            "cad_files": 2,
            "review_packets": 2,
            "ai_calls": 0,
        },
    },
    "design_partner": {
        "plan_code": "design_partner",
        "name": "Design partner",
        "description": (
            "Scoped design-partner pilot for a single firm providing real usage "
            "and feedback."
        ),
        "price_display": "Pilot",
        "sort_order": 1,
        "limits": {
            "projects": 5,
            "documents": 100,
            "pdf_pages": 2000,
            "cad_files": 50,
            "review_packets": 25,
            "ai_calls": 0,
        },
    },
    "professional": {
        "plan_code": "professional",
        "name": "Professional",
        "description": (
            "For a civil/AEC firm running pre-submittal QA across active "
            "projects."
        ),
        "price_display": "Contact us",
        "sort_order": 2,
        "limits": {
            "projects": 50,
            "documents": 2000,
            "pdf_pages": 50000,
            "cad_files": 1000,
            "review_packets": 500,
            "ai_calls": 0,
        },
    },
    "team": {
        "plan_code": "team",
        "name": "Team",
        "description": (
            "For a larger team or a municipal review group with higher volume."
        ),
        "price_display": "Contact us",
        "sort_order": 3,
        "limits": {
            "projects": None,
            "documents": None,
            "pdf_pages": None,
            "cad_files": None,
            "review_packets": None,
            "ai_calls": 0,
        },
    },
}

DEFAULT_PLAN_CODE = "demo"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def list_plans() -> list[dict[str, Any]]:
    """Return the public plan catalog, ordered for display."""

    return sorted(
        (dict(plan) for plan in PLAN_DEFINITIONS.values()),
        key=lambda p: p["sort_order"],
    )


def get_plan(plan_code: str) -> dict[str, Any]:
    """Return a plan definition, falling back to the demo plan if unknown."""

    return PLAN_DEFINITIONS.get(plan_code, PLAN_DEFINITIONS[DEFAULT_PLAN_CODE])


def get_or_create_subscription(
    db: Session, organization_id: str
) -> models.OrganizationSubscription:
    """Return the organization's subscription, creating a default demo one.

    The default subscription is the demo plan with inactive status: billing is
    not active and no payment is collected. This is idempotent.
    """

    sub = (
        db.query(models.OrganizationSubscription)
        .filter(
            models.OrganizationSubscription.organization_id == organization_id
        )
        .first()
    )
    if sub is None:
        now = _now()
        sub = models.OrganizationSubscription(
            subscription_id=f"sub_{_short()}",
            organization_id=organization_id,
            plan_code=DEFAULT_PLAN_CODE,
            status="inactive",
            created_at=now,
            updated_at=now,
        )
        db.add(sub)
        db.flush()
    return sub


def set_subscription_plan(
    db: Session,
    organization_id: str,
    *,
    plan_code: str,
    status: str = "inactive",
) -> models.OrganizationSubscription:
    """Set an organization's plan and status. Used by admin/test paths only.

    This does not process a payment. It records billing posture. Production paid
    activation is deferred to a future Stripe integration.
    """

    from app.core.safety import ALLOWED_PLAN_CODES, ALLOWED_SUBSCRIPTION_STATUSES

    if plan_code not in ALLOWED_PLAN_CODES:
        raise ValueError(f"Invalid plan_code '{plan_code}'.")
    if status not in ALLOWED_SUBSCRIPTION_STATUSES:
        raise ValueError(f"Invalid subscription status '{status}'.")
    sub = get_or_create_subscription(db, organization_id)
    sub.plan_code = plan_code
    sub.status = status
    sub.updated_at = _now()
    db.flush()
    return sub


def subscription_public_dict(
    sub: models.OrganizationSubscription,
) -> dict[str, Any]:
    """Return a safe subscription dict. The Stripe customer id is not exposed."""

    plan = get_plan(sub.plan_code)
    return {
        "subscription_id": sub.subscription_id,
        "organization_id": sub.organization_id,
        "plan_code": sub.plan_code,
        "plan_name": plan["name"],
        "status": sub.status,
        "current_period_end": sub.current_period_end,
        "limits": plan["limits"],
    }


def billing_status(settings: Settings | None = None) -> dict[str, Any]:
    """Return an honest billing-activation status. No secret is included."""

    settings = settings or get_settings()
    enabled = settings.billing_enabled
    return {
        "enabled": enabled,
        "mode": (
            ("test" if settings.STRIPE_TEST_MODE else "live")
            if enabled
            else "inactive"
        ),
        "message": (
            "Billing is configured."
            if enabled
            else (
                "Billing is not active. The billing foundation is in place, but "
                "checkout is deferred until a Stripe key is configured. No "
                "payment is collected."
            )
        ),
    }
