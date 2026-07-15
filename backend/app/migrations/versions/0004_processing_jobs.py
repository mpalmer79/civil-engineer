"""Durable background processing job queue table.

Revision ID: 0004_processing_jobs
Revises: 0003_billing_events
Create Date: 2026-07-15

Adds the `processing_jobs` table, which persists deferred file-processing work
(PDF page indexing and DXF metadata parsing) so it can run on a background
worker instead of the request thread. It stores no file bytes, secrets, or
credentials: only a job type, project scope, a small non-sensitive payload,
lifecycle status, retry bookkeeping, a safe error reason, and the request
correlation id.

The table is created from its SQLAlchemy model definition so the migration stays
in sync with the model, scoped explicitly to the table added here. create/drop
use checkfirst so the migration is safe to apply on a database created by the
create_all convenience path. No existing table is altered or dropped, so no
existing data is affected.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# Importing models registers every table on Base.metadata, including the new one.
from app.db import models

# revision identifiers, used by Alembic.
revision: str = "0004_processing_jobs"
down_revision: str | None = "0003_billing_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_TABLES = (models.ProcessingJob.__table__,)


def upgrade() -> None:
    """Create the processing_jobs table if it does not already exist."""

    bind = op.get_bind()
    for table in _NEW_TABLES:
        table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Drop the processing_jobs table if present."""

    bind = op.get_bind()
    for table in reversed(_NEW_TABLES):
        table.drop(bind=bind, checkfirst=True)
