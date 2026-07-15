"""Shared router, access guards, and raw-id project resolvers.

Access control: project-scoped routes guard on the path project_id. Routes keyed
by a raw entity id (review cycle, resubmittal, comparison run, applicant response,
resolution record) resolve the owning project first so a raw id cannot bypass
tenant access. The public Brookside Meadows demo project stays readable. No
endpoint verifies CAD, validates design, certifies compliance, or makes a final
engineering decision, and there is no action called approve.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import review_cycle_service
from app.services.access_control_service import (
    require_project_read,
    require_project_reviewer,
)
from app.services.review_cycle_service import ReviewCycleError

router = APIRouter(tags=["review-cycle"])

User = models.UserAccount | None


def _handle(exc: ReviewCycleError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


# Raw-id project resolvers. Each returns the owning project_id or None if the
# entity is missing (the service then raises its own 404 for mutations).


def _cycle_pid(db: Session, review_cycle_id: str) -> str | None:
    record = review_cycle_service.get_review_cycle_record(db, review_cycle_id)
    return record.project_id if record is not None else None


def _resub_pid(db: Session, resubmittal_package_id: str) -> str | None:
    record = review_cycle_service.get_resubmittal_package_record(
        db, resubmittal_package_id
    )
    return record.project_id if record is not None else None


def _comparison_pid(db: Session, comparison_run_id: str) -> str | None:
    record = review_cycle_service.get_revision_comparison_run_record(
        db, comparison_run_id
    )
    return record.project_id if record is not None else None


def _applicant_pid(db: Session, applicant_response_id: str) -> str | None:
    record = db.execute(
        select(models.ApplicantResponse).where(
            models.ApplicantResponse.applicant_response_id == applicant_response_id
        )
    ).scalar_one_or_none()
    return record.project_id if record is not None else None


def _resolution_pid(db: Session, resolution_record_id: str) -> str | None:
    record = db.execute(
        select(models.ResponseResolutionRecord).where(
            models.ResponseResolutionRecord.resolution_record_id
            == resolution_record_id
        )
    ).scalar_one_or_none()
    return record.project_id if record is not None else None


def _guard_read(db: Session, project_id: str | None, user: User, missing: str) -> None:
    if project_id is None:
        raise HTTPException(status_code=404, detail=missing)
    require_project_read(db, project_id, user)


def _guard_reviewer_if_found(db: Session, project_id: str | None, user: User) -> None:
    # The downstream service raises its own 404 when the entity is missing, so
    # only enforce access when the owning project resolved.
    if project_id is not None:
        require_project_reviewer(db, project_id, user)
