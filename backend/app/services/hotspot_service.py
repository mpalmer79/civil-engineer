"""Read operations for homepage hotspots."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def list_hotspots(db: Session, project_id: str) -> list[models.Hotspot]:
    stmt = (
        select(models.Hotspot)
        .where(models.Hotspot.project_id == project_id)
        .order_by(models.Hotspot.hotspot_id)
    )
    return list(db.scalars(stmt).all())
