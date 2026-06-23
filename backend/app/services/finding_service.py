"""Read operations for review-support findings."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def list_findings(db: Session, project_id: str) -> list[models.Finding]:
    stmt = (
        select(models.Finding)
        .where(models.Finding.project_id == project_id)
        .order_by(models.Finding.finding_id)
    )
    return list(db.scalars(stmt).all())


def get_finding(db: Session, finding_id: str) -> models.Finding | None:
    return db.get(models.Finding, finding_id)
