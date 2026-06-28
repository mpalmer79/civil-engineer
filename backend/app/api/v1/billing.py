"""Billing, subscription, and usage API routes (Production Phase 4B/4C).

Exposes the public plan catalog, an organization's subscription posture and
advisory usage summary, and an honest checkout endpoint that reports billing as
inactive while live Stripe is deferred. No route returns a Stripe key or any
secret, and no real payment is processed.

A plan or subscription status is an account-posture label only. It never implies
a review outcome, approval, certification, or compliance.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.db.database import get_db
from app.schemas.billing import (
    BillingStatusResponse,
    CheckoutResponse,
    OrganizationBillingResponse,
    PlanResponse,
    SubscriptionResponse,
    UsageSummaryResponse,
)
from app.services import billing_service, usage_service
from app.services.access_control_service import (
    get_optional_user,
    require_org_member,
)

router = APIRouter(tags=["billing"])


@router.get("/billing/plans", response_model=list[PlanResponse])
def list_plans() -> list[PlanResponse]:
    """Return the public plan catalog with advisory limits."""

    return [PlanResponse(**plan) for plan in billing_service.list_plans()]


@router.get("/billing/status", response_model=BillingStatusResponse)
def billing_status() -> BillingStatusResponse:
    """Return the honest billing-activation status. No secret is included."""

    return BillingStatusResponse(**billing_service.billing_status())


@router.get(
    "/organizations/{organization_id}/billing",
    response_model=OrganizationBillingResponse,
)
def organization_billing(
    organization_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> OrganizationBillingResponse:
    """Return an organization's subscription, billing status, and plans.

    Requires organization membership.
    """

    require_org_member(db, organization_id, user)
    sub = billing_service.get_or_create_subscription(db, organization_id)
    db.commit()
    return OrganizationBillingResponse(
        subscription=SubscriptionResponse(
            **billing_service.subscription_public_dict(sub)
        ),
        billing=BillingStatusResponse(**billing_service.billing_status()),
        plans=[PlanResponse(**plan) for plan in billing_service.list_plans()],
    )


@router.get(
    "/organizations/{organization_id}/usage",
    response_model=UsageSummaryResponse,
)
def organization_usage(
    organization_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> UsageSummaryResponse:
    """Return an organization's advisory usage summary. Requires membership."""

    require_org_member(db, organization_id, user)
    return UsageSummaryResponse(
        **usage_service.usage_summary(db, organization_id)
    )


@router.post(
    "/organizations/{organization_id}/billing/checkout",
    response_model=CheckoutResponse,
)
def start_checkout(
    organization_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    """Start a checkout session, or report billing as inactive when deferred.

    While billing is deferred (no Stripe key configured), this returns an honest
    inactive response with no checkout URL, so the UI shows a disabled state
    rather than a button that would error. No payment is processed.
    """

    require_org_member(db, organization_id, user)
    settings = get_settings()
    if not settings.billing_enabled:
        return CheckoutResponse(
            available=False,
            detail=(
                "Billing is not active yet. Checkout is deferred until a Stripe "
                "key is configured. No payment is collected."
            ),
            checkout_url=None,
        )
    # Stripe is configured but live checkout creation is intentionally deferred to
    # the next phase. Report unavailable rather than create a partial session.
    return CheckoutResponse(
        available=False,
        detail=(
            "A Stripe key is configured, but hosted checkout is not enabled in "
            "this build. Contact us to activate a plan."
        ),
        checkout_url=None,
    )
