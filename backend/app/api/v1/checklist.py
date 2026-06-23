"""Checklist API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.checklist import ChecklistItemRead
from app.services import checklist_service, project_service

router = APIRouter(tags=["checklist"])


@router.get(
    "/projects/{project_id}/checklist", response_model=list[ChecklistItemRead]
)
def list_checklist(
    project_id: str, db: Session = Depends(get_db)
) -> list[ChecklistItemRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return checklist_service.list_checklist_items(db, project_id)


@router.get(
    "/checklist/{checklist_item_id}", response_model=ChecklistItemRead
)
def get_checklist_item(
    checklist_item_id: str, db: Session = Depends(get_db)
) -> ChecklistItemRead:
    item = checklist_service.get_checklist_item(db, checklist_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return item
