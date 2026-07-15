"""Response resolution record endpoints."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.review_cycle import (
    ResolutionSummary,
    ResponseResolutionCreate,
    ResponseResolutionRecordRead,
    ResponseResolutionStatusUpdate,
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
    _resolution_pid,
    router,
)


@router.post(
    "/review-cycles/{review_cycle_id}/resolution-records",
    response_model=ResponseResolutionRecordRead,
)
def create_resolution_record(
    review_cycle_id: str,
    body: ResponseResolutionCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseResolutionRecordRead:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return review_cycle_service.create_response_resolution_record(
            db,
            review_cycle_id,
            response_package_item_id=body.response_package_item_id,
            workflow_item_id=body.workflow_item_id,
            applicant_response_id=body.applicant_response_id,
            revision_change_record_id=body.revision_change_record_id,
            status=body.status,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.patch(
    "/resolution-records/{resolution_record_id}/status",
    response_model=ResponseResolutionRecordRead,
)
def update_resolution_status(
    resolution_record_id: str,
    body: ResponseResolutionStatusUpdate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseResolutionRecordRead:
    _guard_reviewer_if_found(db, _resolution_pid(db, resolution_record_id), user)
    try:
        return review_cycle_service.update_response_resolution_status(
            db,
            resolution_record_id,
            status=body.status,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/resolution-records",
    response_model=list[ResponseResolutionRecordRead],
)
def list_resolution_records(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResponseResolutionRecordRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_response_resolution_records(db, project_id)


@router.get(
    "/review-cycles/{review_cycle_id}/resolution-summary",
    response_model=ResolutionSummary,
)
def get_resolution_summary(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResolutionSummary:
    _guard_read(db, _cycle_pid(db, review_cycle_id), user, "Review cycle not found")
    try:
        return ResolutionSummary.model_validate(
            review_cycle_service.get_resolution_summary(db, review_cycle_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc
