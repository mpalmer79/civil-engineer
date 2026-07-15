"""Revision comparison endpoints.

Revision comparison compares extracted DXF metadata only. No endpoint verifies
CAD, validates design, certifies compliance, or makes a final engineering
decision.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.review_cycle import (
    RevisionChangeRecordRead,
    RevisionComparisonCreate,
    RevisionComparisonRunRead,
    RevisionComparisonSummary,
)
from app.services import project_service, review_cycle_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.review_cycle_service import ReviewCycleError

from app.api.v1.review_cycle._common import (
    User,
    _comparison_pid,
    _guard_read,
    _handle,
    router,
)


@router.post(
    "/review-cycles/{review_cycle_id}/revision-comparisons",
    response_model=RevisionComparisonRunRead,
)
def run_revision_comparison(
    review_cycle_id: str,
    body: RevisionComparisonCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> RevisionComparisonRunRead:
    cycle = review_cycle_service.get_review_cycle_record(db, review_cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    require_project_reviewer(db, cycle.project_id, user)
    try:
        return review_cycle_service.run_revision_comparison(
            db,
            project_id=cycle.project_id,
            review_cycle_id=review_cycle_id,
            previous_parse_run_id=body.previous_parse_run_id,
            current_parse_run_id=body.current_parse_run_id,
            resubmittal_package_id=body.resubmittal_package_id,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/revision-comparisons",
    response_model=list[RevisionComparisonRunRead],
)
def list_revision_comparisons(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[RevisionComparisonRunRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_revision_comparison_runs(db, project_id)


@router.get(
    "/revision-comparisons/{comparison_run_id}",
    response_model=RevisionComparisonRunRead,
)
def get_revision_comparison(
    comparison_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> RevisionComparisonRunRead:
    _guard_read(
        db, _comparison_pid(db, comparison_run_id), user, "Comparison run not found"
    )
    run = review_cycle_service.get_revision_comparison_run(db, comparison_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Comparison run not found")
    return run


@router.get(
    "/revision-comparisons/{comparison_run_id}/changes",
    response_model=list[RevisionChangeRecordRead],
)
def list_revision_changes(
    comparison_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[RevisionChangeRecordRead]:
    _guard_read(
        db, _comparison_pid(db, comparison_run_id), user, "Comparison run not found"
    )
    return review_cycle_service.list_revision_change_records(db, comparison_run_id)


@router.get(
    "/revision-comparisons/{comparison_run_id}/summary",
    response_model=RevisionComparisonSummary,
)
def get_revision_comparison_summary(
    comparison_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> RevisionComparisonSummary:
    _guard_read(
        db, _comparison_pid(db, comparison_run_id), user, "Comparison run not found"
    )
    result = review_cycle_service.summarize_revision_changes(db, comparison_run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Comparison run not found")
    return RevisionComparisonSummary.model_validate(result)
