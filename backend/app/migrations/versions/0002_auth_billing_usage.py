"""Auth lifecycle, team invitations, and billing/usage tables.

Revision ID: 0002_auth_billing_usage
Revises: 0001_initial_schema
Create Date: 2026-06-28

Production Phase 4B/4C adds the account-lifecycle and billing-readiness schema:

- password_reset_tokens: hashed password reset tokens with expiry and use-once.
- organization_invitations: hashed team invitation tokens with role, status, and
  expiry.
- organization_subscriptions: per-organization billing posture (plan and status)
  with reserved, nullable Stripe mapping columns.
- usage_events: append-only internal usage ledger for advisory limits.

The four tables are created from their SQLAlchemy model definitions so the
migration stays in sync with the models, scoped explicitly to the tables added in
this phase. create/drop use checkfirst so the migration is safe to apply on a
database created by the create_all convenience path (where the tables may already
exist) and on a database stamped at the previous revision before these models
existed. No existing table is altered or dropped, so no pilot or project data is
affected.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# Importing models registers every table on Base.metadata, including the four
# new tables this migration manages.
from app.db import models

# revision identifiers, used by Alembic.
revision: str = "0002_auth_billing_usage"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The tables added in this phase, in dependency-safe creation order.
_NEW_TABLES = (
    models.PasswordResetToken.__table__,
    models.OrganizationInvitation.__table__,
    models.OrganizationSubscription.__table__,
    models.UsageEvent.__table__,
)


def upgrade() -> None:
    """Create the Phase 4B/4C tables if they do not already exist."""

    bind = op.get_bind()
    for table in _NEW_TABLES:
        table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Drop the Phase 4B/4C tables if present, in reverse order."""

    bind = op.get_bind()
    for table in reversed(_NEW_TABLES):
        table.drop(bind=bind, checkfirst=True)
