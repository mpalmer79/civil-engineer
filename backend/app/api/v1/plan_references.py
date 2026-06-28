"""Plan reference API routes for the Phase 6 foundation.

These endpoints expose seeded plan references and the subset whose target is
missing, conflicting, or unclear. They surface review-support evidence and do
not make final decisions.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.plan_reference import PlanReferenceRead
from app.services import plan_consistency_service, project_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
)

router = APIRouter(tags=["plan-references"])


@router.get(
    "/projects/{project_id}/plan-references",
    response_model=list[PlanReferenceRead],
)
def list_plan_references(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[PlanReferenceRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return plan_consistency_service.list_plan_references(db, project_id)


@router.get(
    "/projects/{project_id}/plan-references/inconsistencies",
    response_model=list[PlanReferenceRead],
)
def list_plan_reference_inconsistencies(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[PlanReferenceRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return plan_consistency_service.list_inconsistencies(db, project_id)
