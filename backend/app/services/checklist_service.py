"""Read operations for checklist items."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def list_checklist_items(db: Session, project_id: str) -> list[models.ChecklistItem]:
    stmt = (
        select(models.ChecklistItem)
        .where(models.ChecklistItem.project_id == project_id)
        .order_by(models.ChecklistItem.checklist_item_id)
    )
    return list(db.scalars(stmt).all())


def get_checklist_item(
    db: Session, checklist_item_id: str
) -> models.ChecklistItem | None:
    return db.get(models.ChecklistItem, checklist_item_id)
