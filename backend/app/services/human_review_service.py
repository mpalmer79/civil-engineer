"""Human review service for AI draft findings.

This service persists human review actions on AI draft findings and applies the
allowed status transitions. It enforces the professional boundary: only valid
draft findings can be accepted or edited, failed drafts can only be rejected,
escalated, or marked unclear, edited text must still pass prohibited-word
checks, and no action produces final engineering approval language.

Every action keeps the finding under human control and writes audit events so
the decision history is preserved.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ACTIONS_REQUIRING_VALID_DRAFT,
    ALLOWED_REVIEW_ACTIONS,
    REVIEW_ACTION_TO_STATUS,
    find_prohibited_language,
)
from app.db import models


class ReviewActionError(Exception):
    """Raised when a requested review action is not allowed.

    The status code lets the API layer return the right HTTP response without
    leaking service internals.
    """

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_hr_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type="reviewer",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def list_human_review_queue(
    db: Session, project_id: str
) -> list[models.AIDraftFinding]:
    """Return all draft findings for a project for the human review queue.

    Both valid drafts awaiting review and failed drafts are returned so the UI
    can group them by status and show failures separately. Ordering keeps
    pending items (requires_human_review and validation_failed) first.
    """

    stmt = (
        select(models.AIDraftFinding)
        .where(models.AIDraftFinding.project_id == project_id)
        .order_by(models.AIDraftFinding.created_at.desc())
    )
    drafts = list(db.scalars(stmt).all())
    pending = {"requires_human_review", "validation_failed"}
    drafts.sort(key=lambda d: 0 if d.status in pending else 1)
    return drafts


def list_review_actions_for_draft(
    db: Session, draft_finding_id: str
) -> list[models.HumanReviewAction]:
    stmt = (
        select(models.HumanReviewAction)
        .where(models.HumanReviewAction.draft_finding_id == draft_finding_id)
        .order_by(models.HumanReviewAction.created_at)
    )
    return list(db.scalars(stmt).all())


def list_review_actions_for_project(
    db: Session, project_id: str
) -> list[models.HumanReviewAction]:
    stmt = (
        select(models.HumanReviewAction)
        .where(models.HumanReviewAction.project_id == project_id)
        .order_by(models.HumanReviewAction.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def _validate_action(
    draft: models.AIDraftFinding,
    *,
    action: str,
    reviewer_name: str,
    reviewer_note: str,
) -> None:
    if action not in ALLOWED_REVIEW_ACTIONS:
        raise ReviewActionError(
            f"Unknown review action '{action}'.", status_code=422
        )
    if not reviewer_name or not reviewer_name.strip():
        raise ReviewActionError("reviewer_name is required.", status_code=422)
    if not reviewer_note or not reviewer_note.strip():
        raise ReviewActionError("reviewer_note is required.", status_code=422)

    draft_is_valid = draft.validation_status == "validation_passed"
    if action in ACTIONS_REQUIRING_VALID_DRAFT and not draft_is_valid:
        raise ReviewActionError(
            "A failed draft finding cannot be accepted or edited. It may only "
            "be rejected, escalated, or marked unclear pending regeneration.",
            status_code=409,
        )


def apply_review_action(
    db: Session,
    *,
    draft_finding_id: str,
    action: str,
    reviewer_name: str,
    reviewer_note: str,
    edited_title: str | None = None,
    edited_summary: str | None = None,
    edited_recommended_action: str | None = None,
) -> tuple[models.HumanReviewAction, models.AIDraftFinding]:
    """Validate and persist a human review action on a draft finding."""

    draft = db.scalars(
        select(models.AIDraftFinding).where(
            models.AIDraftFinding.draft_finding_id == draft_finding_id
        )
    ).first()
    if draft is None:
        raise ReviewActionError("Draft finding not found.", status_code=404)

    previous_status = draft.status

    _audit(
        db,
        project_id=draft.project_id,
        event_type="human_review_action_started",
        related_entity_type="ai_draft_finding",
        related_entity_id=draft_finding_id,
        description=(
            f"Human review action '{action}' started by {reviewer_name}."
        ),
        metadata={
            "review_run_id": draft.review_run_id,
            "draft_finding_id": draft_finding_id,
            "action": action,
            "reviewer_name": reviewer_name,
            "previous_status": previous_status,
            "validation_status": draft.validation_status,
            "safety_status": draft.safety_check_status,
        },
    )

    _validate_action(
        draft,
        action=action,
        reviewer_name=reviewer_name,
        reviewer_note=reviewer_note,
    )

    # Edited findings must still pass prohibited-word checks before any edit is
    # applied. The check runs over every reviewer-supplied field.
    if action == "edited":
        prohibited: list[str] = []
        for text in (edited_title, edited_summary, edited_recommended_action):
            prohibited.extend(find_prohibited_language(text))
        if prohibited:
            _audit(
                db,
                project_id=draft.project_id,
                event_type="edited_finding_safety_check_failed",
                related_entity_type="ai_draft_finding",
                related_entity_id=draft_finding_id,
                description=(
                    "Edited finding failed the prohibited-word safety check. "
                    "No edit was applied."
                ),
                metadata={"prohibited_words": sorted(set(prohibited))},
            )
            db.commit()
            raise ReviewActionError(
                "Edited text contains prohibited final-decision wording: "
                + ", ".join(sorted(set(prohibited))),
                status_code=422,
            )
        _audit(
            db,
            project_id=draft.project_id,
            event_type="edited_finding_safety_check_passed",
            related_entity_type="ai_draft_finding",
            related_entity_id=draft_finding_id,
            description="Edited finding passed the prohibited-word safety check.",
        )

    new_status = REVIEW_ACTION_TO_STATUS[action]

    # Apply edited fields to the draft so the reviewer-corrected text becomes the
    # finding text. The finding still remains a review-support finding under
    # human control.
    if action == "edited":
        if edited_title and edited_title.strip():
            draft.title = edited_title.strip()
        if edited_summary and edited_summary.strip():
            draft.summary = edited_summary.strip()
        if edited_recommended_action and edited_recommended_action.strip():
            draft.recommended_human_action = edited_recommended_action.strip()

    draft.status = new_status

    review_action_id = f"hra_{uuid.uuid4().hex[:12]}"
    record = models.HumanReviewAction(
        review_action_id=review_action_id,
        draft_finding_id=draft_finding_id,
        project_id=draft.project_id,
        review_run_id=draft.review_run_id,
        reviewer_name=reviewer_name.strip(),
        action=action,
        reviewer_note=reviewer_note.strip(),
        edited_title=edited_title,
        edited_summary=edited_summary,
        edited_recommended_action=edited_recommended_action,
        previous_status=previous_status,
        new_status=new_status,
    )
    db.add(record)

    _audit(
        db,
        project_id=draft.project_id,
        event_type="human_review_action_recorded",
        related_entity_type="human_review_action",
        related_entity_id=review_action_id,
        description=(
            f"Human review action '{action}' recorded by {reviewer_name}."
        ),
        metadata={
            "review_run_id": draft.review_run_id,
            "draft_finding_id": draft_finding_id,
            "review_action_id": review_action_id,
            "action": action,
            "reviewer_name": reviewer_name,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )
    _audit(
        db,
        project_id=draft.project_id,
        event_type="draft_finding_status_updated",
        related_entity_type="ai_draft_finding",
        related_entity_id=draft_finding_id,
        description=(
            f"Draft finding status updated from {previous_status} to "
            f"{new_status}."
        ),
        metadata={
            "review_action_id": review_action_id,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )

    db.commit()
    db.refresh(record)
    db.refresh(draft)
    return record, draft
