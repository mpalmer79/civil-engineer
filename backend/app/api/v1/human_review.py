"""Human review API routes for AI draft findings.

These endpoints expose the human review queue and persist reviewer actions with
status transitions. No endpoint approves, certifies, or finalizes an engineering
decision, and there is no action called approve. Every action keeps the finding
under human control and writes audit events.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.ai_review import AIDraftFindingRead
from app.schemas.human_review import (
    HumanReviewActionRead,
    ReviewActionCreate,
    ReviewActionResult,
)
from app.services import ai_review_service, human_review_service, project_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.human_review_service import ReviewActionError

router = APIRouter(tags=["human-review"])


@router.get(
    "/projects/{project_id}/human-review-queue",
    response_model=list[AIDraftFindingRead],
)
def get_human_review_queue(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[AIDraftFindingRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return human_review_service.list_human_review_queue(db, project_id)


@router.post(
    "/draft-findings/{draft_finding_id}/review-actions",
    response_model=ReviewActionResult,
)
def create_review_action(
    draft_finding_id: str,
    body: ReviewActionCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewActionResult:
    draft = ai_review_service.get_draft_finding(db, draft_finding_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft finding not found")
    require_project_reviewer(db, draft.project_id, user)
    try:
        action, draft = human_review_service.apply_review_action(
            db,
            draft_finding_id=draft_finding_id,
            action=body.action,
            reviewer_name=body.reviewer_name,
            reviewer_note=body.reviewer_note,
            edited_title=body.edited_title,
            edited_summary=body.edited_summary,
            edited_recommended_action=body.edited_recommended_action,
        )
    except ReviewActionError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return ReviewActionResult(action=action, draft_finding=draft)


@router.get(
    "/draft-findings/{draft_finding_id}/review-actions",
    response_model=list[HumanReviewActionRead],
)
def list_draft_review_actions(
    draft_finding_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[HumanReviewActionRead]:
    draft = ai_review_service.get_draft_finding(db, draft_finding_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft finding not found")
    require_project_read(db, draft.project_id, user)
    return human_review_service.list_review_actions_for_draft(
        db, draft_finding_id
    )


@router.get(
    "/projects/{project_id}/review-actions",
    response_model=list[HumanReviewActionRead],
)
def list_project_review_actions(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[HumanReviewActionRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return human_review_service.list_review_actions_for_project(db, project_id)
