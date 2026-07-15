"""Shared project and checklist item lookup helpers.

These lookups are reused across the checklist review package submodules
(project checklist reads, item review actions, evidence links, and draft
findings). Keeping them in one place preserves a single source of truth for the
not-found guards.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.checklist_review_service.errors import ChecklistReviewError


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise ChecklistReviewError("Project not found.", status_code=404)
    return project


def _checklist_items(
    db: Session, project_checklist_id: str
) -> list[models.ProjectChecklistItem]:
    return list(
        db.scalars(
            select(models.ProjectChecklistItem)
            .where(
                models.ProjectChecklistItem.project_checklist_id
                == project_checklist_id
            )
            .order_by(models.ProjectChecklistItem.sort_order)
        ).all()
    )


def get_checklist_item(
    db: Session, project_id: str, project_checklist_item_id: str
) -> models.ProjectChecklistItem:
    item = db.get(models.ProjectChecklistItem, project_checklist_item_id)
    if item is None or item.project_id != project_id:
        raise ChecklistReviewError("Checklist item not found.", status_code=404)
    return item
