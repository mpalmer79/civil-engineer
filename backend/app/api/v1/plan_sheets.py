"""Plan sheet, CAD-aware metadata, and plan consistency API routes (Phase 6).

These endpoints expose the seeded Brookside Meadows plan sheet index, CAD-aware
feature metadata, plan references, and the plan consistency check. All responses
use review-support language. No endpoint approves, certifies, or verifies a CAD
drawing, and every plan consistency finding requires human review.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.plan_sheet import (
    CADMetadataRead,
    PlanConsistencyFindingRead,
    PlanConsistencySummary,
    PlanReferenceRead,
    PlanSheetRead,
    PlanSheetSummary,
)
from app.services import (
    cad_metadata_service,
    plan_consistency_service,
    plan_sheet_service,
    project_service,
)
from app.services.plan_consistency_service import PlanConsistencyError

router = APIRouter(tags=["plan-sheets"])


def _require_project(db: Session, project_id: str) -> None:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get(
    "/projects/{project_id}/plan-sheets",
    response_model=list[PlanSheetRead],
)
def list_plan_sheets(
    project_id: str, db: Session = Depends(get_db)
) -> list[PlanSheetRead]:
    _require_project(db, project_id)
    return plan_sheet_service.list_plan_sheets(db, project_id)


@router.get(
    "/projects/{project_id}/plan-sheets/summary",
    response_model=PlanSheetSummary,
)
def plan_sheet_summary(
    project_id: str, db: Session = Depends(get_db)
) -> PlanSheetSummary:
    _require_project(db, project_id)
    return plan_sheet_service.plan_sheet_summary(db, project_id)


@router.get("/plan-sheets/{sheet_id}", response_model=PlanSheetRead)
def get_plan_sheet(
    sheet_id: str, db: Session = Depends(get_db)
) -> PlanSheetRead:
    sheet = plan_sheet_service.get_plan_sheet(db, sheet_id)
    if sheet is None:
        raise HTTPException(status_code=404, detail="Plan sheet not found")
    return sheet


@router.get(
    "/projects/{project_id}/cad-metadata",
    response_model=list[CADMetadataRead],
)
def list_cad_metadata(
    project_id: str,
    entity_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CADMetadataRead]:
    _require_project(db, project_id)
    return cad_metadata_service.list_cad_metadata(
        db, project_id, entity_type=entity_type
    )


@router.get(
    "/plan-sheets/{sheet_id}/cad-metadata",
    response_model=list[CADMetadataRead],
)
def list_sheet_cad_metadata(
    sheet_id: str, db: Session = Depends(get_db)
) -> list[CADMetadataRead]:
    if plan_sheet_service.get_plan_sheet(db, sheet_id) is None:
        raise HTTPException(status_code=404, detail="Plan sheet not found")
    return cad_metadata_service.list_cad_metadata_for_sheet(db, sheet_id)


@router.get(
    "/projects/{project_id}/plan-references",
    response_model=list[PlanReferenceRead],
)
def list_plan_references(
    project_id: str, db: Session = Depends(get_db)
) -> list[PlanReferenceRead]:
    _require_project(db, project_id)
    return plan_consistency_service.list_plan_references(db, project_id)


@router.get(
    "/projects/{project_id}/plan-references/inconsistencies",
    response_model=list[PlanReferenceRead],
)
def list_plan_reference_inconsistencies(
    project_id: str, db: Session = Depends(get_db)
) -> list[PlanReferenceRead]:
    _require_project(db, project_id)
    return plan_consistency_service.list_inconsistent_references(db, project_id)


@router.post(
    "/projects/{project_id}/plan-consistency-check",
    response_model=list[PlanConsistencyFindingRead],
)
def run_plan_consistency_check(
    project_id: str, db: Session = Depends(get_db)
) -> list[PlanConsistencyFindingRead]:
    _require_project(db, project_id)
    try:
        return plan_consistency_service.run_consistency_check(db, project_id)
    except PlanConsistencyError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc


@router.get(
    "/projects/{project_id}/plan-consistency-findings",
    response_model=list[PlanConsistencyFindingRead],
)
def list_plan_consistency_findings(
    project_id: str, db: Session = Depends(get_db)
) -> list[PlanConsistencyFindingRead]:
    _require_project(db, project_id)
    return plan_consistency_service.list_plan_consistency_findings(
        db, project_id
    )


@router.get(
    "/projects/{project_id}/plan-consistency-summary",
    response_model=PlanConsistencySummary,
)
def plan_consistency_summary(
    project_id: str, db: Session = Depends(get_db)
) -> PlanConsistencySummary:
    _require_project(db, project_id)
    return plan_consistency_service.plan_consistency_summary(db, project_id)


@router.get(
    "/plan-consistency-findings/{plan_finding_id}",
    response_model=PlanConsistencyFindingRead,
)
def get_plan_consistency_finding(
    plan_finding_id: str, db: Session = Depends(get_db)
) -> PlanConsistencyFindingRead:
    finding = plan_consistency_service.get_plan_consistency_finding(
        db, plan_finding_id
    )
    if finding is None:
        raise HTTPException(
            status_code=404, detail="Plan consistency finding not found"
        )
    return finding
