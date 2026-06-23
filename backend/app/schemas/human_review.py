"""Pydantic schemas for human review actions on AI draft findings."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.ai_review import AIDraftFindingRead


class ReviewActionCreate(BaseModel):
    """Request body for recording a human review action.

    The action must be one of the allowed review-support actions. There is no
    action called approve. Edited fields are optional and only used when the
    action is edited.
    """

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
    """The recorded action and the updated draft finding it produced."""

    action: HumanReviewActionRead
    draft_finding: AIDraftFindingRead
