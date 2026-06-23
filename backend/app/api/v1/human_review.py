"""Human review queue and review action API routes.

These endpoints record reviewer decisions on AI draft findings and return the
human review queue. No endpoint approves, certifies, or declares a design
compliant: an accepted finding remains a review-support finding under human
control. There is intentionally no endpoint named approve.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.human_review import (
    HumanReviewActionRead,
    HumanReviewQueue,
    HumanReviewQueueItem,
    ReviewActionCreate,
    ReviewActionResult,
)
from app.services import ai_review_service, human_review_service, project_service
from app.services.human_review_service import ReviewActionError

router = APIRouter(tags=["human-review"])


def _to_queue_item(item: dict) -> HumanReviewQueueItem:
    return HumanReviewQueueItem(
        draft_finding=item["draft_finding"],
        checklist_item_id=item["checklist_item_id"],
        is_failed_draft=item["is_failed_draft"],
        needs_review=item["needs_review"],
        latest_status=item["latest_status"],
        review_actions=item["review_actions"],
    )


@router.get(
    "/projects/{project_id}/human-review-queue",
    response_model=HumanReviewQueue,
)
def get_human_review_queue(
    project_id: str, db: Session = Depends(get_db)
) -> HumanReviewQueue:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    groups = human_review_service.build_human_review_queue(db, project_id)
    needs = [_to_queue_item(i) for i in groups.needs_review]
    reviewed = [_to_queue_item(i) for i in groups.reviewed]
    failures = [_to_queue_item(i) for i in groups.validation_failures]
    return HumanReviewQueue(
        project_id=project_id,
        needs_review=needs,
        reviewed=reviewed,
        validation_failures=failures,
        needs_review_count=len(needs),
        reviewed_count=len(reviewed),
        validation_failure_count=len(failures),
    )


@router.post(
    "/draft-findings/{draft_finding_id}/review-actions",
    response_model=ReviewActionResult,
)
def create_review_action(
    draft_finding_id: str,
    body: ReviewActionCreate,
    db: Session = Depends(get_db),
) -> ReviewActionResult:
    draft = ai_review_service.get_draft_finding(db, draft_finding_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft finding not found")
    try:
        action, updated = human_review_service.record_review_action(
            db,
            draft=draft,
            action=body.action,
            reviewer_name=body.reviewer_name,
            reviewer_note=body.reviewer_note,
            edited_title=body.edited_title,
            edited_summary=body.edited_summary,
            edited_recommended_action=body.edited_recommended_action,
        )
    except ReviewActionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReviewActionResult(review_action=action, draft_finding=updated)


@router.get(
    "/draft-findings/{draft_finding_id}/review-actions",
    response_model=list[HumanReviewActionRead],
)
def list_draft_review_actions(
    draft_finding_id: str, db: Session = Depends(get_db)
) -> list[HumanReviewActionRead]:
    if ai_review_service.get_draft_finding(db, draft_finding_id) is None:
        raise HTTPException(status_code=404, detail="Draft finding not found")
    return human_review_service.list_actions_for_draft(db, draft_finding_id)


@router.get(
    "/projects/{project_id}/review-actions",
    response_model=list[HumanReviewActionRead],
)
def list_project_review_actions(
    project_id: str, db: Session = Depends(get_db)
) -> list[HumanReviewActionRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return human_review_service.list_actions_for_project(db, project_id)
