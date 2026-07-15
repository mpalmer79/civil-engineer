"""Applicant response and mapping endpoints."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.review_cycle import (
    ApplicantResponseMappingCreate,
    ApplicantResponseMappingRead,
    ApplicantResponseRead,
    ResponseMappingSummary,
)
from app.services import project_service, review_cycle_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
)
from app.services.review_cycle_service import ReviewCycleError

from app.api.v1.review_cycle._common import (
    User,
    _applicant_pid,
    _cycle_pid,
    _guard_read,
    _guard_reviewer_if_found,
    _handle,
    router,
)


@router.get(
    "/projects/{project_id}/applicant-responses",
    response_model=list[ApplicantResponseRead],
)
def list_applicant_responses(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ApplicantResponseRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_applicant_responses(db, project_id)


@router.post(
    "/applicant-responses/{applicant_response_id}/mappings",
    response_model=ApplicantResponseMappingRead,
)
def create_applicant_response_mapping(
    applicant_response_id: str,
    body: ApplicantResponseMappingCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ApplicantResponseMappingRead:
    _guard_reviewer_if_found(db, _applicant_pid(db, applicant_response_id), user)
    try:
        return review_cycle_service.create_applicant_response_mapping(
            db,
            applicant_response_id,
            response_package_item_id=body.response_package_item_id,
            workflow_item_id=body.workflow_item_id,
            mapping_confidence=body.mapping_confidence,
            mapping_reason=body.mapping_reason,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.post(
    "/review-cycles/{review_cycle_id}/suggest-response-mappings",
    response_model=list[ApplicantResponseMappingRead],
)
def suggest_response_mappings(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ApplicantResponseMappingRead]:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return review_cycle_service.auto_suggest_response_mappings(
            db, review_cycle_id
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/review-cycles/{review_cycle_id}/response-mapping-summary",
    response_model=ResponseMappingSummary,
)
def get_response_mapping_summary(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMappingSummary:
    _guard_read(db, _cycle_pid(db, review_cycle_id), user, "Review cycle not found")
    try:
        return ResponseMappingSummary.model_validate(
            review_cycle_service.get_response_mapping_summary(db, review_cycle_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc
