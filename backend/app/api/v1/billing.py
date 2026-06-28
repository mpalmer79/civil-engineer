"""Billing, subscription, usage, and Stripe API routes (Phase 4B/4C/4D).

Exposes the public plan catalog, an organization's subscription posture and
advisory usage summary, an org-admin checkout endpoint that creates a Stripe
Checkout session when configured (and reports an honest unavailable state
otherwise), and a signature-verified Stripe webhook endpoint.

No route returns a Stripe key, a webhook secret, or any secret, and no real
payment is processed unless Stripe is configured. A plan or subscription status
is an account-posture label only; it never implies a review outcome, approval,
certification, or compliance.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import log_event
from app.db import models
from app.db.database import get_db
from app.schemas.billing import (
    BillingStatusResponse,
    CheckoutResponse,
    OrganizationBillingResponse,
    PlanResponse,
    SubscriptionResponse,
    UsageSummaryResponse,
    WebhookAckResponse,
)
from app.services import billing_service, stripe_service, usage_service
from app.services.access_control_service import (
    get_optional_user,
    require_org_admin,
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
    settings = get_settings()
    sub = billing_service.get_or_create_subscription(db, organization_id)
    db.commit()
    return OrganizationBillingResponse(
        subscription=SubscriptionResponse(
            **billing_service.subscription_public_dict(sub)
        ),
        billing=BillingStatusResponse(**billing_service.billing_status()),
        plans=[PlanResponse(**plan) for plan in billing_service.list_plans()],
        checkout_available=settings.stripe_checkout_configured,
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
    """Return an organization's usage summary. Requires membership."""

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
    """Start a Stripe Checkout session for the professional plan.

    Requires an organization admin. Returns a checkout URL only when Stripe is
    fully configured; otherwise returns an honest unavailable response so the UI
    shows a disabled state rather than a button that would error. No payment is
    processed when Stripe is not configured.
    """

    require_org_admin(db, organization_id, user)
    settings = get_settings()
    if not settings.stripe_checkout_configured:
        return CheckoutResponse(
            available=False,
            detail=(
                "Billing is not active in this environment. Checkout becomes "
                "available when Stripe is configured. No payment is collected."
            ),
            checkout_url=None,
        )
    try:
        url = stripe_service.create_checkout_session(
            db, organization_id=organization_id, settings=settings
        )
    except stripe_service.StripeError:
        return CheckoutResponse(
            available=False,
            detail="Checkout is temporarily unavailable. Please try again later.",
            checkout_url=None,
        )
    return CheckoutResponse(
        available=True,
        detail="Checkout session created.",
        checkout_url=url,
    )


@router.post("/billing/webhook", response_model=WebhookAckResponse)
async def stripe_webhook(
    request: Request, db: Session = Depends(get_db)
) -> WebhookAckResponse:
    """Receive and process a Stripe webhook with signature verification.

    The raw body and the Stripe-Signature header are verified against
    STRIPE_WEBHOOK_SECRET. An invalid or missing signature is rejected with 400.
    Verified events are processed idempotently by event id. No secret, signature,
    or raw payload is logged.
    """

    settings = get_settings()
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe_service.verify_webhook_signature(
            payload, signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe_service.StripeError:
        # Reject without echoing any signature or secret detail.
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    result = stripe_service.handle_event(db, event)
    log_event(
        "stripe_webhook_processed",
        event_type=result.get("event_type", ""),
        status=result.get("status", ""),
    )
    return WebhookAckResponse(
        received=True,
        status=result.get("status", "ignored"),
    )
