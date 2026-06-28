"""Stripe billing integration (Production Phase 4D).

Minimal, safe Stripe support for one paid plan (professional):

- Checkout session creation uses the Stripe SDK and is isolated here so business
  logic never imports a vendor client. It runs only when checkout is fully
  configured.
- Webhook signature verification is implemented with the standard library (the
  documented Stripe HMAC scheme) so the security-critical path is deterministic
  and testable without the SDK or any network call.
- Webhook events are processed idempotently: each Stripe event id is recorded in
  `billing_events`, and a duplicate delivery is ignored.

No Stripe secret, signature, or raw payload is logged or stored. A subscription
status is an account-posture label only and never implies a review outcome.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import models
from app.services import billing_service

# Stripe subscription statuses mapped onto our account-posture labels.
_STATUS_MAP = {
    "active": "active",
    "trialing": "trialing",
    "past_due": "past_due",
    "canceled": "canceled",
    "unpaid": "past_due",
    "incomplete": "inactive",
    "incomplete_expired": "canceled",
}

# The plan a paid checkout maps to in this phase.
_CHECKOUT_PLAN_CODE = "professional"

# Webhook events this phase processes. Other events are acknowledged and ignored.
HANDLED_EVENT_TYPES = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}


class StripeError(Exception):
    """Raised for a Stripe configuration or signature problem."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def map_subscription_status(stripe_status: str) -> str:
    """Map a Stripe subscription status onto our subscription status set."""

    return _STATUS_MAP.get((stripe_status or "").strip().lower(), "inactive")


# ---------------------------------------------------------------------------
# Checkout (Stripe SDK, isolated)
# ---------------------------------------------------------------------------


def _stripe_client(settings: Settings):
    """Return the configured Stripe SDK module. Imported lazily and isolated."""

    import stripe  # noqa: PLC0415 - lazy import so the SDK is optional locally

    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_checkout_session(
    db: Session, *, organization_id: str, settings: Settings | None = None
) -> str:
    """Create a Stripe Checkout session for the professional plan; return its URL.

    Ensures the organization has a Stripe customer mapping, reusing an existing
    one. Raises StripeError when checkout is not configured. The Stripe secret is
    never returned or logged.
    """

    settings = settings or get_settings()
    if not settings.stripe_checkout_configured:
        raise StripeError("Stripe checkout is not configured.")

    sub = billing_service.get_or_create_subscription(db, organization_id)
    stripe = _stripe_client(settings)

    customer_id = sub.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            metadata={"organization_id": organization_id}
        )
        customer_id = customer["id"]
        sub.stripe_customer_id = customer_id
        sub.updated_at = _now()
        db.flush()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        client_reference_id=organization_id,
        line_items=[{"price": settings.STRIPE_PRICE_PROFESSIONAL, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        metadata={"organization_id": organization_id},
        subscription_data={"metadata": {"organization_id": organization_id}},
    )
    db.commit()
    return session["url"]


# ---------------------------------------------------------------------------
# Webhook signature verification (standard library)
# ---------------------------------------------------------------------------


def _parse_signature_header(header: str) -> tuple[int | None, list[str]]:
    timestamp: int | None = None
    signatures: list[str] = []
    for part in (header or "").split(","):
        key, _, value = part.partition("=")
        key = key.strip()
        value = value.strip()
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                timestamp = None
        elif key == "v1":
            signatures.append(value)
    return timestamp, signatures


def verify_webhook_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
    *,
    tolerance_seconds: int = 300,
    now: int | None = None,
) -> dict[str, Any]:
    """Verify a Stripe webhook signature and return the parsed event.

    Implements the documented Stripe scheme: the signed payload is
    "{timestamp}.{raw_body}" and the expected signature is its HMAC-SHA256 keyed
    by the webhook secret. Raises StripeError on a missing, malformed, expired, or
    mismatched signature. No secret is logged.
    """

    if not secret:
        raise StripeError("Webhook secret is not configured.")
    timestamp, signatures = _parse_signature_header(signature_header)
    if timestamp is None or not signatures:
        raise StripeError("Missing or malformed signature header.")
    current = now if now is not None else int(time.time())
    if abs(current - timestamp) > tolerance_seconds:
        raise StripeError("Signature timestamp outside tolerance.")
    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    expected = hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()
    if not any(hmac.compare_digest(expected, sig) for sig in signatures):
        raise StripeError("Signature mismatch.")
    try:
        return json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise StripeError("Invalid webhook payload.") from exc


# ---------------------------------------------------------------------------
# Webhook event processing (idempotent)
# ---------------------------------------------------------------------------


def _resolve_organization_id(
    db: Session, obj: dict[str, Any]
) -> str | None:
    """Resolve the organization from a Stripe object, never trusting one source."""

    metadata = obj.get("metadata") or {}
    org_id = obj.get("client_reference_id") or metadata.get("organization_id")
    if org_id:
        return org_id
    customer_id = obj.get("customer")
    if customer_id:
        sub = db.scalars(
            select(models.OrganizationSubscription).where(
                models.OrganizationSubscription.stripe_customer_id == customer_id
            )
        ).first()
        if sub is not None:
            return sub.organization_id
    return None


def _apply_subscription_object(
    db: Session, org_id: str, obj: dict[str, Any], *, deleted: bool = False
) -> None:
    sub = billing_service.get_or_create_subscription(db, org_id)
    customer_id = obj.get("customer")
    if customer_id:
        sub.stripe_customer_id = customer_id
    subscription_id = obj.get("id")
    if subscription_id:
        sub.stripe_subscription_id = subscription_id
    if deleted:
        sub.status = "canceled"
    else:
        sub.status = map_subscription_status(obj.get("status", ""))
        sub.plan_code = _CHECKOUT_PLAN_CODE
    period_end = obj.get("current_period_end")
    if isinstance(period_end, (int, float)):
        sub.current_period_end = datetime.fromtimestamp(
            period_end, tz=timezone.utc
        )
    sub.updated_at = _now()
    db.flush()


def handle_event(db: Session, event: dict[str, Any]) -> dict[str, Any]:
    """Process a verified Stripe event idempotently. Returns a safe result.

    Duplicate events (by Stripe event id) are ignored. Unhandled event types are
    acknowledged without changing state. Subscription state is mapped onto the
    organization's subscription record.
    """

    event_id = event.get("id")
    event_type = event.get("type", "")
    if not event_id:
        raise StripeError("Event is missing an id.")

    existing = db.scalars(
        select(models.BillingEvent).where(
            models.BillingEvent.stripe_event_id == event_id
        )
    ).first()
    if existing is not None:
        return {"status": "duplicate", "event_type": event_type}

    obj = (event.get("data") or {}).get("object") or {}
    org_id: str | None = None
    applied = False

    if event_type in HANDLED_EVENT_TYPES:
        org_id = _resolve_organization_id(db, obj)
        if org_id is not None:
            if event_type == "checkout.session.completed":
                # The session references the customer and (for subscription mode)
                # the subscription id. Mark the org active on completion.
                sub = billing_service.get_or_create_subscription(db, org_id)
                if obj.get("customer"):
                    sub.stripe_customer_id = obj["customer"]
                if obj.get("subscription"):
                    sub.stripe_subscription_id = obj["subscription"]
                sub.plan_code = _CHECKOUT_PLAN_CODE
                sub.status = "active"
                sub.updated_at = _now()
                db.flush()
                applied = True
            elif event_type == "customer.subscription.deleted":
                _apply_subscription_object(db, org_id, obj, deleted=True)
                applied = True
            else:
                _apply_subscription_object(db, org_id, obj)
                applied = True

    db.add(
        models.BillingEvent(
            billing_event_id=f"bev_{_short()}",
            stripe_event_id=event_id,
            event_type=event_type,
            organization_id=org_id,
            created_at=_now(),
            processed_at=_now(),
        )
    )
    db.commit()
    return {
        "status": "processed" if applied else "ignored",
        "event_type": event_type,
    }
