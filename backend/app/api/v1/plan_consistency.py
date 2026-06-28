"""Plan consistency API routes for the Phase 6 foundation.

These endpoints run the plan consistency check, list the generated findings, and
return a single finding. The check evaluates seeded references and sheets and
produces review-support findings that require human review. It does not perform
final design review, verify CAD drawings, or certify compliance.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.plan_consistency import (
    PlanConsistencyCheckResult,
    PlanConsistencyFindingRead,
)
from app.services import plan_consistency_service, project_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)

router = APIRouter(tags=["plan-consistency"])


@router.post(
    "/projects/{project_id}/plan-consistency-check",
    response_model=PlanConsistencyCheckResult,
)
def run_plan_consistency_check(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PlanConsistencyCheckResult:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    # Running the check regenerates review-support findings, so require reviewer.
    require_project_reviewer(db, project_id, user)
    summary = plan_consistency_service.run_consistency_check(db, project_id)
    return PlanConsistencyCheckResult(**summary)


@router.get(
    "/projects/{project_id}/plan-consistency-findings",
    response_model=list[PlanConsistencyFindingRead],
)
def list_plan_consistency_findings(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[PlanConsistencyFindingRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return plan_consistency_service.list_plan_consistency_findings(db, project_id)


@router.get(
    "/projects/{project_id}/plan-consistency-summary",
    response_model=PlanConsistencyCheckResult,
)
def get_plan_consistency_summary(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PlanConsistencyCheckResult:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return PlanConsistencyCheckResult(
        **plan_consistency_service.plan_consistency_summary(db, project_id)
    )


@router.get(
    "/plan-consistency-findings/{plan_finding_id}",
    response_model=PlanConsistencyFindingRead,
)
def get_plan_consistency_finding(
    plan_finding_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PlanConsistencyFindingRead:
    finding = plan_consistency_service.get_plan_consistency_finding(
        db, plan_finding_id
    )
    if finding is None:
        raise HTTPException(
            status_code=404, detail="Plan consistency finding not found"
        )
    # Resolve the owning project so a raw finding id cannot bypass access.
    require_project_read(db, finding.project_id, user)
    return finding
