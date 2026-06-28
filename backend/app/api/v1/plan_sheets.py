"""Plan sheet API routes for the Phase 6 plan sheet index.

These endpoints expose the seeded Brookside Meadows plan sheet index and its
summary. They organize plan sheet metadata for human review and do not perform
final design review or verify CAD drawings.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.cad_metadata import CadMetadataRead
from app.schemas.plan_sheet import PlanSheetRead, PlanSheetSummary
from app.services import cad_metadata_service, plan_sheet_service, project_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
)

router = APIRouter(tags=["plan-sheets"])


@router.get(
    "/projects/{project_id}/plan-sheets",
    response_model=list[PlanSheetRead],
)
def list_plan_sheets(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[PlanSheetRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return plan_sheet_service.list_plan_sheets(db, project_id)


@router.get(
    "/projects/{project_id}/plan-sheets/summary",
    response_model=PlanSheetSummary,
)
def get_plan_sheet_summary(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PlanSheetSummary:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return PlanSheetSummary(**plan_sheet_service.plan_sheet_summary(db, project_id))


@router.get("/plan-sheets/{sheet_id}", response_model=PlanSheetRead)
def get_plan_sheet(
    sheet_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PlanSheetRead:
    sheet = plan_sheet_service.get_plan_sheet(db, sheet_id)
    if sheet is None:
        raise HTTPException(status_code=404, detail="Plan sheet not found")
    # Resolve the owning project so a raw sheet id cannot bypass access.
    require_project_read(db, sheet.project_id, user)
    return sheet


@router.get(
    "/plan-sheets/{sheet_id}/cad-metadata",
    response_model=list[CadMetadataRead],
)
def list_sheet_cad_metadata(
    sheet_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadMetadataRead]:
    sheet = plan_sheet_service.get_plan_sheet(db, sheet_id)
    if sheet is None:
        raise HTTPException(status_code=404, detail="Plan sheet not found")
    require_project_read(db, sheet.project_id, user)
    return cad_metadata_service.list_cad_metadata_for_sheet(db, sheet_id)
