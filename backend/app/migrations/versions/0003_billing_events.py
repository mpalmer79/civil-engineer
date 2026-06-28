"""Billing event idempotency table for Stripe webhooks.

Revision ID: 0003_billing_events
Revises: 0002_auth_billing_usage
Create Date: 2026-06-28

Production Phase 4D adds the `billing_events` table, which records processed
Stripe webhook event ids so duplicate deliveries are ignored. It stores no Stripe
secret, signature, or raw payload.

The table is created from its SQLAlchemy model definition so the migration stays
in sync with the model, scoped explicitly to the table added in this phase.
create/drop use checkfirst so the migration is safe to apply on a database
created by the create_all convenience path. No existing table is altered or
dropped, so no existing data is affected.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# Importing models registers every table on Base.metadata, including the new one.
from app.db import models

# revision identifiers, used by Alembic.
revision: str = "0003_billing_events"
down_revision: str | None = "0002_auth_billing_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_TABLES = (models.BillingEvent.__table__,)


def upgrade() -> None:
    """Create the billing_events table if it does not already exist."""

    bind = op.get_bind()
    for table in _NEW_TABLES:
        table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Drop the billing_events table if present."""

    bind = op.get_bind()
    for table in reversed(_NEW_TABLES):
        table.drop(bind=bind, checkfirst=True)
