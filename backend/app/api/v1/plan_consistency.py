"""Plan consistency API routes for the Phase 6 foundation.

These endpoints run the plan consistency check, list the generated findings, and
return a single finding. The check evaluates seeded references and sheets and
produces review-support findings that require human review. It does not perform
final design review, verify CAD drawings, or certify compliance.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.plan_consistency import (
    PlanConsistencyCheckResult,
    PlanConsistencyFindingRead,
)
from app.services import plan_consistency_service, project_service

router = APIRouter(tags=["plan-consistency"])


@router.post(
    "/projects/{project_id}/plan-consistency-check",
    response_model=PlanConsistencyCheckResult,
)
def run_plan_consistency_check(
    project_id: str, db: Session = Depends(get_db)
) -> PlanConsistencyCheckResult:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    summary = plan_consistency_service.run_consistency_check(db, project_id)
    return PlanConsistencyCheckResult(**summary)


@router.get(
    "/projects/{project_id}/plan-consistency-findings",
    response_model=list[PlanConsistencyFindingRead],
)
def list_plan_consistency_findings(
    project_id: str, db: Session = Depends(get_db)
) -> list[PlanConsistencyFindingRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return plan_consistency_service.list_plan_consistency_findings(db, project_id)


@router.get(
    "/projects/{project_id}/plan-consistency-summary",
    response_model=PlanConsistencyCheckResult,
)
def get_plan_consistency_summary(
    project_id: str, db: Session = Depends(get_db)
) -> PlanConsistencyCheckResult:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return PlanConsistencyCheckResult(
        **plan_consistency_service.plan_consistency_summary(db, project_id)
    )


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
