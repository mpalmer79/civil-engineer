"""Read operations for audit events."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def list_audit_events(db: Session, project_id: str) -> list[models.AuditEvent]:
    stmt = (
        select(models.AuditEvent)
        .where(models.AuditEvent.project_id == project_id)
        .order_by(models.AuditEvent.timestamp)
    )
    return list(db.scalars(stmt).all())
