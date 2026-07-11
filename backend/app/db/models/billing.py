"""Billing domain: organization subscriptions, usage events, and Stripe
billing events (test mode scaffolding)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

class OrganizationSubscription(Base):
    __tablename__ = "organization_subscriptions"

    # One subscription posture per organization. plan_code is one of
    # ALLOWED_PLAN_CODES; status is one of ALLOWED_SUBSCRIPTION_STATUSES. The
    # stripe_* columns are nullable mapping fields reserved for a future Stripe
    # integration; they are unused while billing is deferred and never hold a
    # secret key.
    subscription_id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.organization_id"), nullable=False, unique=True
    )
    plan_code: Mapped[str] = mapped_column(String, nullable=False, default="demo")
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="inactive"
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )


class UsageEvent(Base):
    __tablename__ = "usage_events"

    # Append-only internal usage ledger. category is one of
    # ALLOWED_USAGE_CATEGORIES; quantity is a positive count. organization_id is
    # nullable so global events (for example a public pilot request) can be
    # recorded without a tenant. No file content, document text, or secret is
    # ever stored here.
    usage_event_id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class BillingEvent(Base):
    __tablename__ = "billing_events"

    # Idempotency ledger for processed Stripe webhook events (Production Phase
    # 4D). stripe_event_id is unique so a duplicate webhook delivery is ignored.
    # No Stripe secret, signature, or raw payload is stored here; only the event
    # id, type, and the organization it mapped to. processed_at records when the
    # event was applied to the organization subscription.
    billing_event_id: Mapped[str] = mapped_column(String, primary_key=True)
    stripe_event_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    organization_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
