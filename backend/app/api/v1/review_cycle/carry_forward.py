"""Issue carry-forward endpoints."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.review_cycle import (
    CarryForwardResult,
    CarryForwardSummary,
    IssueCarryForwardCreate,
    IssueCarryForwardRead,
)
from app.services import project_service, review_cycle_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
)
from app.services.review_cycle_service import ReviewCycleError

from app.api.v1.review_cycle._common import (
    User,
    _cycle_pid,
    _guard_read,
    _guard_reviewer_if_found,
    _handle,
    router,
)


@router.post(
    "/review-cycles/{review_cycle_id}/carry-forward",
    response_model=CarryForwardResult,
)
def carry_forward(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CarryForwardResult:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return CarryForwardResult.model_validate(
            review_cycle_service.carry_forward_unresolved_items(db, review_cycle_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.post(
    "/review-cycles/{review_cycle_id}/carry-forward-items",
    response_model=IssueCarryForwardRead,
)
def create_carry_forward_item(
    review_cycle_id: str,
    body: IssueCarryForwardCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> IssueCarryForwardRead:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return review_cycle_service.create_issue_carry_forward(
            db,
            review_cycle_id,
            source_workflow_item_id=body.source_workflow_item_id,
            source_response_item_id=body.source_response_item_id,
            source_cad_finding_id=body.source_cad_finding_id,
            source_revision_change_id=body.source_revision_change_id,
            title=body.title,
            reason=body.reason,
            reviewer_name=body.reviewer_name,
            reviewer_note=body.reviewer_note,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/carry-forwards",
    response_model=list[IssueCarryForwardRead],
)
def list_carry_forwards(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[IssueCarryForwardRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_issue_carry_forwards(db, project_id)


@router.get(
    "/review-cycles/{review_cycle_id}/carry-forward-summary",
    response_model=CarryForwardSummary,
)
def get_carry_forward_summary(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CarryForwardSummary:
    _guard_read(db, _cycle_pid(db, review_cycle_id), user, "Review cycle not found")
    try:
        return CarryForwardSummary.model_validate(
            review_cycle_service.get_carry_forward_summary(db, review_cycle_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc
