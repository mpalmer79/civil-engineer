"""Next-cycle preparation endpoints."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.review_cycle import NextCyclePreparationRead
from app.services import review_cycle_service
from app.services.access_control_service import get_optional_user
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
    "/review-cycles/{review_cycle_id}/prepare-next-cycle",
    response_model=NextCyclePreparationRead,
)
def prepare_next_cycle(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> NextCyclePreparationRead:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return review_cycle_service.prepare_next_cycle(db, review_cycle_id)
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/review-cycles/{review_cycle_id}/next-cycle-preparation",
    response_model=NextCyclePreparationRead,
)
def get_next_cycle_preparation(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> NextCyclePreparationRead:
    _guard_read(db, _cycle_pid(db, review_cycle_id), user, "Review cycle not found")
    try:
        prep = review_cycle_service.get_next_cycle_preparation(db, review_cycle_id)
    except ReviewCycleError as exc:
        raise _handle(exc) from exc
    if prep is None:
        raise HTTPException(
            status_code=404, detail="Next cycle preparation not found"
        )
    return prep
