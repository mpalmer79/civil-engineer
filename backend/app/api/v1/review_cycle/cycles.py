"""Review cycle endpoints."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.review_cycle import (
    ReviewCycleCreate,
    ReviewCycleDashboard,
    ReviewCycleRead,
    ReviewCycleSummary,
)
from app.services import project_service, review_cycle_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.review_cycle_service import ReviewCycleError

from app.api.v1.review_cycle._common import User, _handle, router


@router.post(
    "/projects/{project_id}/review-cycles", response_model=ReviewCycleRead
)
def create_review_cycle(
    project_id: str,
    body: ReviewCycleCreate | None = None,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewCycleRead:
    require_project_reviewer(db, project_id, user)
    payload = body or ReviewCycleCreate()
    try:
        return review_cycle_service.create_review_cycle(
            db,
            project_id=project_id,
            cycle_number=payload.cycle_number,
            cycle_name=payload.cycle_name,
            source_response_package_id=payload.source_response_package_id,
            source_workflow_board_id=payload.source_workflow_board_id,
            summary=payload.summary,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/review-cycles",
    response_model=list[ReviewCycleRead],
)
def list_review_cycles(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ReviewCycleRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_review_cycles(db, project_id)


@router.get("/review-cycles/{review_cycle_id}", response_model=ReviewCycleRead)
def get_review_cycle(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewCycleRead:
    cycle = review_cycle_service.get_review_cycle(db, review_cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    require_project_read(db, cycle.project_id, user)
    return cycle


@router.get(
    "/projects/{project_id}/review-cycle-summary",
    response_model=ReviewCycleSummary,
)
def get_review_cycle_summary(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewCycleSummary:
    require_project_read(db, project_id, user)
    try:
        return ReviewCycleSummary.model_validate(
            review_cycle_service.get_review_cycle_summary(db, project_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/review-cycle-dashboard",
    response_model=ReviewCycleDashboard,
)
def get_review_cycle_dashboard(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewCycleDashboard:
    require_project_read(db, project_id, user)
    try:
        return ReviewCycleDashboard.model_validate(
            review_cycle_service.get_review_cycle_dashboard(db, project_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc
