"""Checklist API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.checklist import ChecklistItemRead
from app.services import checklist_service, project_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
)

router = APIRouter(tags=["checklist"])


@router.get(
    "/projects/{project_id}/checklist", response_model=list[ChecklistItemRead]
)
def list_checklist(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ChecklistItemRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return checklist_service.list_checklist_items(db, project_id)


@router.get(
    "/checklist/{checklist_item_id}", response_model=ChecklistItemRead
)
def get_checklist_item(
    checklist_item_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ChecklistItemRead:
    item = checklist_service.get_checklist_item(db, checklist_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    # Resolve the owning project so a raw item id cannot bypass access.
    require_project_read(db, item.project_id, user)
    return item
