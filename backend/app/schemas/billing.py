"""Pydantic schemas for billing and usage (Production Phase 4B/4C).

These describe the billing-readiness foundation and advisory usage metering.
Billing is deferred: a subscription status is an account-posture label, not a
review outcome. No schema carries a secret, a Stripe key, or any file content.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PlanResponse(BaseModel):
    plan_code: str
    name: str
    description: str
    price_display: str
    sort_order: int
    limits: dict[str, int | None]


class BillingStatusResponse(BaseModel):
    enabled: bool
    mode: str
    message: str


class SubscriptionResponse(BaseModel):
    subscription_id: str
    organization_id: str
    plan_code: str
    plan_name: str
    status: str
    current_period_end: datetime | None = None
    limits: dict[str, int | None]


class OrganizationBillingResponse(BaseModel):
    subscription: SubscriptionResponse
    billing: BillingStatusResponse
    plans: list[PlanResponse]
    # True when Stripe checkout is fully configured. The UI shows the checkout CTA
    # only when this is true; otherwise it shows an honest unavailable state.
    checkout_available: bool = False


class UsageLimitItem(BaseModel):
    key: str
    category: str
    used: int
    limit: int | None = None
    status: str
    enforced: bool = False


class UsageSummaryResponse(BaseModel):
    organization_id: str
    plan_code: str
    plan_name: str
    subscription_status: str
    enforcement: str
    limits: list[UsageLimitItem]
    totals: dict[str, int]


class CheckoutResponse(BaseModel):
    # Honest checkout response. available is true only when Stripe checkout is
    # configured and a session URL was created; otherwise available is false and
    # no URL is returned, so the UI shows an unavailable state rather than a
    # button that would error.
    available: bool
    detail: str
    checkout_url: str | None = None


class WebhookAckResponse(BaseModel):
    # Acknowledgement returned to Stripe after a verified webhook. Carries no
    # secret and no event payload, only that the event was received and its
    # processing outcome (processed, duplicate, ignored).
    received: bool
    status: str
