"""Human review service for AI draft findings.

This service records reviewer decisions on AI draft findings and applies the
resulting status transition. It enforces the professional boundary:

* Only valid draft findings can be accepted or edited.
* Failed draft findings can be rejected, escalated, marked unclear, or have more
  information requested, but never accepted as valid review findings.
* Every action requires a reviewer note.
* Edited text is checked for prohibited final-decision wording before it is
  saved, and the safety check is audited either way.
* No action produces final engineering approval language. An accepted finding
  remains a review-support finding that a reviewer has accepted, not a certified
  or compliant conclusion.

Every action writes audit events so the decision history is preserved.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ACTIONS_REQUIRING_VALID_DRAFT,
    HUMAN_REVIEW_ACTIONS,
    find_prohibited_language,
)
from app.db import models


class ReviewActionError(Exception):
    """Raised when a requested review action is not allowed."""


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
            actor_type="human_reviewer",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def list_actions_for_draft(
    db: Session, draft_finding_id: str
) -> list[models.HumanReviewAction]:
    stmt = (
        select(models.HumanReviewAction)
        .where(models.HumanReviewAction.draft_finding_id == draft_finding_id)
        .order_by(models.HumanReviewAction.created_at)
    )
    return list(db.scalars(stmt).all())


def list_actions_for_project(
    db: Session, project_id: str
) -> list[models.HumanReviewAction]:
    stmt = (
        select(models.HumanReviewAction)
        .where(models.HumanReviewAction.project_id == project_id)
        .order_by(models.HumanReviewAction.created_at.desc())
    )
    return list(db.scalars(stmt).all())


@dataclass
class QueueGroups:
    needs_review: list[dict]
    reviewed: list[dict]
    validation_failures: list[dict]


def build_human_review_queue(db: Session, project_id: str) -> QueueGroups:
    """Group a project's draft findings into the human review queue.

    Valid drafts that still carry the ``requires_human_review`` status are listed
    as needing review. Valid drafts that already have a recorded action are
    listed as reviewed. Failed drafts are surfaced separately as validation
    failures and are never presented as usable review findings.
    """

    stmt = (
        select(models.AIDraftFinding)
        .where(models.AIDraftFinding.project_id == project_id)
        .order_by(models.AIDraftFinding.created_at.desc())
    )
    drafts = list(db.scalars(stmt).all())

    actions_by_draft: dict[str, list[models.HumanReviewAction]] = {}
    for action in list_actions_for_project(db, project_id):
        actions_by_draft.setdefault(action.draft_finding_id, []).append(action)

    needs_review: list[dict] = []
    reviewed: list[dict] = []
    validation_failures: list[dict] = []

    for draft in drafts:
        actions = sorted(
            actions_by_draft.get(draft.draft_finding_id, []),
            key=lambda a: a.created_at,
        )
        is_failed = draft.validation_status == "validation_failed"
        needs = (
            not is_failed and draft.status == "requires_human_review"
        )
        item = {
            "draft_finding": draft,
            "checklist_item_id": draft.checklist_item_id,
            "is_failed_draft": is_failed,
            "needs_review": needs,
            "latest_status": draft.status,
            "review_actions": actions,
        }
        if is_failed:
            validation_failures.append(item)
        elif needs:
            needs_review.append(item)
        else:
            reviewed.append(item)

    return QueueGroups(
        needs_review=needs_review,
        reviewed=reviewed,
        validation_failures=validation_failures,
    )


def record_review_action(
    db: Session,
    *,
    draft: models.AIDraftFinding,
    action: str,
    reviewer_name: str,
    reviewer_note: str,
    edited_title: str | None = None,
    edited_summary: str | None = None,
    edited_recommended_action: str | None = None,
) -> tuple[models.HumanReviewAction, models.AIDraftFinding]:
    """Validate and record a human review action, applying the status change."""

    reviewer_name = (reviewer_name or "").strip()
    reviewer_note = (reviewer_note or "").strip()

    # Validate the action and its inputs.
    if action not in HUMAN_REVIEW_ACTIONS:
        raise ReviewActionError(
            f"Unknown review action '{action}'. Allowed actions: "
            + ", ".join(sorted(HUMAN_REVIEW_ACTIONS))
        )
    if not reviewer_name:
        raise ReviewActionError("A reviewer name is required.")
    if not reviewer_note:
        raise ReviewActionError("A reviewer note is required for every action.")

    is_failed = draft.validation_status == "validation_failed"
    if action in ACTIONS_REQUIRING_VALID_DRAFT and is_failed:
        raise ReviewActionError(
            f"A failed draft finding cannot be '{action}'. It can only be "
            "rejected, escalated, marked unclear, or have more information "
            "requested."
        )

    previous_status = draft.status
    new_status = HUMAN_REVIEW_ACTIONS[action]

    _audit(
        db,
        project_id=draft.project_id,
        event_type="human_review_action_started",
        related_entity_type="ai_draft_finding",
        related_entity_id=draft.draft_finding_id,
        description=(
            f"Reviewer {reviewer_name} started a '{action}' action on draft "
            f"{draft.draft_finding_id}."
        ),
        metadata={
            "review_run_id": draft.review_run_id,
            "reviewer_name": reviewer_name,
            "action": action,
            "previous_status": previous_status,
            "validation_status": draft.validation_status,
            "safety_status": draft.safety_check_status,
        },
    )

    # Edited text must pass the prohibited-word safety check before it is saved.
    if action == "edited":
        edited_fields = {
            "edited_title": edited_title,
            "edited_summary": edited_summary,
            "edited_recommended_action": edited_recommended_action,
        }
        prohibited: list[str] = []
        for text in edited_fields.values():
            prohibited.extend(find_prohibited_language(text))
        if prohibited:
            _audit(
                db,
                project_id=draft.project_id,
                event_type="edited_finding_safety_check_failed",
                related_entity_type="ai_draft_finding",
                related_entity_id=draft.draft_finding_id,
                description=(
                    "Edited draft finding failed the prohibited-word safety "
                    "check and was not saved."
                ),
                metadata={
                    "review_run_id": draft.review_run_id,
                    "reviewer_name": reviewer_name,
                    "prohibited_words": sorted(set(prohibited)),
                },
            )
            db.commit()
            raise ReviewActionError(
                "Edited finding contains prohibited final-decision wording: "
                + ", ".join(sorted(set(prohibited)))
            )
        _audit(
            db,
            project_id=draft.project_id,
            event_type="edited_finding_safety_check_passed",
            related_entity_type="ai_draft_finding",
            related_entity_id=draft.draft_finding_id,
            description="Edited draft finding passed the prohibited-word safety check.",
            metadata={
                "review_run_id": draft.review_run_id,
                "reviewer_name": reviewer_name,
            },
        )
        # Preserve edited fields on the draft so the reviewer copy is canonical.
        if edited_title and edited_title.strip():
            draft.title = edited_title.strip()
        if edited_summary and edited_summary.strip():
            draft.summary = edited_summary.strip()
        if edited_recommended_action and edited_recommended_action.strip():
            draft.recommended_human_action = edited_recommended_action.strip()

    review_action = models.HumanReviewAction(
        review_action_id=f"hra_{uuid.uuid4().hex[:12]}",
        draft_finding_id=draft.draft_finding_id,
        project_id=draft.project_id,
        review_run_id=draft.review_run_id,
        reviewer_name=reviewer_name,
        action=action,
        reviewer_note=reviewer_note,
        edited_title=edited_title,
        edited_summary=edited_summary,
        edited_recommended_action=edited_recommended_action,
        previous_status=previous_status,
        new_status=new_status,
    )
    db.add(review_action)

    draft.status = new_status

    _audit(
        db,
        project_id=draft.project_id,
        event_type="human_review_action_recorded",
        related_entity_type="human_review_action",
        related_entity_id=review_action.review_action_id,
        description=(
            f"Recorded '{action}' on draft {draft.draft_finding_id} by "
            f"{reviewer_name}. The finding remains a review-support finding "
            "under human control."
        ),
        metadata={
            "review_run_id": draft.review_run_id,
            "draft_finding_id": draft.draft_finding_id,
            "review_action_id": review_action.review_action_id,
            "reviewer_name": reviewer_name,
            "action": action,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )
    _audit(
        db,
        project_id=draft.project_id,
        event_type="draft_finding_status_updated",
        related_entity_type="ai_draft_finding",
        related_entity_id=draft.draft_finding_id,
        description=(
            f"Draft finding status changed from {previous_status} to "
            f"{new_status}."
        ),
        metadata={
            "review_run_id": draft.review_run_id,
            "review_action_id": review_action.review_action_id,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )

    db.commit()
    db.refresh(review_action)
    db.refresh(draft)
    return review_action, draft
