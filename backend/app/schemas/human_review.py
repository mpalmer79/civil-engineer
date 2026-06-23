"""Pydantic schemas for human review actions and the human review queue.

A human review action records a reviewer decision on an AI draft finding. None
of the actions approves, certifies, or declares a design compliant. An accepted
finding remains a review-support finding under human control.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.ai_review import AIDraftFindingRead


class ReviewActionCreate(BaseModel):
    """Request body for recording a human review action."""

    action: str
    reviewer_name: str
    reviewer_note: str
    edited_title: str | None = None
    edited_summary: str | None = None
    edited_recommended_action: str | None = None


class HumanReviewActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_action_id: str
    draft_finding_id: str
    project_id: str
    review_run_id: str
    reviewer_name: str
    action: str
    reviewer_note: str
    edited_title: str | None = None
    edited_summary: str | None = None
    edited_recommended_action: str | None = None
    previous_status: str
    new_status: str
    created_at: datetime


class ReviewActionResult(BaseModel):
    """Response after recording a review action: the action and updated draft."""

    review_action: HumanReviewActionRead
    draft_finding: AIDraftFindingRead


class HumanReviewQueueItem(BaseModel):
    """A draft finding plus its recorded review actions and review state."""

    draft_finding: AIDraftFindingRead
    checklist_item_id: str
    is_failed_draft: bool
    needs_review: bool
    latest_status: str
    review_actions: list[HumanReviewActionRead]


class HumanReviewQueue(BaseModel):
    """Grouped human review queue for a project.

    Valid drafts that still need review are separated from already-reviewed
    drafts. Failed drafts are surfaced separately as validation failures and are
    never presented as usable review findings.
    """

    project_id: str
    needs_review: list[HumanReviewQueueItem]
    reviewed: list[HumanReviewQueueItem]
    validation_failures: list[HumanReviewQueueItem]
    needs_review_count: int
    reviewed_count: int
    validation_failure_count: int
