"""Resubmittal package endpoints."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.review_cycle import (
    ApplicantResponseCreate,
    ApplicantResponseRead,
    ResubmittalPackageCreate,
    ResubmittalPackageDetail,
    ResubmittalPackageRead,
    ResubmittalPackageStatusUpdate,
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
    _guard_read,
    _guard_reviewer_if_found,
    _handle,
    _resub_pid,
    router,
)


@router.post(
    "/projects/{project_id}/resubmittals", response_model=ResubmittalPackageRead
)
def create_resubmittal(
    project_id: str,
    body: ResubmittalPackageCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalPackageRead:
    require_project_reviewer(db, project_id, user)
    try:
        return review_cycle_service.create_resubmittal_package(
            db,
            project_id=project_id,
            review_cycle_id=body.review_cycle_id,
            package_name=body.package_name,
            submitted_by=body.submitted_by,
            summary=body.summary,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/resubmittals",
    response_model=list[ResubmittalPackageRead],
)
def list_resubmittals(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResubmittalPackageRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_resubmittal_packages(db, project_id)


@router.get(
    "/resubmittals/{resubmittal_package_id}",
    response_model=ResubmittalPackageDetail,
)
def get_resubmittal(
    resubmittal_package_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalPackageDetail:
    _guard_read(
        db,
        _resub_pid(db, resubmittal_package_id),
        user,
        "Resubmittal package not found",
    )
    result = review_cycle_service.get_resubmittal_package(
        db, resubmittal_package_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Resubmittal package not found")
    return ResubmittalPackageDetail.model_validate(result)


@router.patch(
    "/resubmittals/{resubmittal_package_id}/status",
    response_model=ResubmittalPackageRead,
)
def update_resubmittal_status(
    resubmittal_package_id: str,
    body: ResubmittalPackageStatusUpdate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalPackageRead:
    _guard_reviewer_if_found(db, _resub_pid(db, resubmittal_package_id), user)
    try:
        return review_cycle_service.update_resubmittal_package_status(
            db,
            resubmittal_package_id,
            status=body.status,
            reviewer_note=body.reviewer_note,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.post(
    "/resubmittals/{resubmittal_package_id}/cad-files/{cad_file_id}",
    response_model=ResubmittalPackageDetail,
)
def link_cad_file(
    resubmittal_package_id: str,
    cad_file_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalPackageDetail:
    _guard_reviewer_if_found(db, _resub_pid(db, resubmittal_package_id), user)
    try:
        review_cycle_service.link_cad_file_to_resubmittal(
            db, resubmittal_package_id, cad_file_id
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc
    result = review_cycle_service.get_resubmittal_package(
        db, resubmittal_package_id
    )
    return ResubmittalPackageDetail.model_validate(result)


@router.post(
    "/resubmittals/{resubmittal_package_id}/applicant-responses",
    response_model=ApplicantResponseRead,
)
def create_applicant_response(
    resubmittal_package_id: str,
    body: ApplicantResponseCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ApplicantResponseRead:
    _guard_reviewer_if_found(db, _resub_pid(db, resubmittal_package_id), user)
    try:
        return review_cycle_service.link_applicant_response_to_resubmittal(
            db,
            resubmittal_package_id,
            response_text=body.response_text,
            response_topic=body.response_topic,
            submitted_by=body.submitted_by,
            target_response_item_id=body.target_response_item_id,
            target_workflow_item_id=body.target_workflow_item_id,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc
