"""Plan consistency review action service for Phase 7.

This service persists human review actions on plan consistency findings. A
reviewer may record needs_follow_up, reviewer_confirmed, not_applicable, or
needs_more_information. There is no action called approve, and no action
approves a plan, certifies compliance, verifies CAD, or validates a design.
Every action keeps the finding a review-support finding under human control and
writes an audit event.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_PLAN_REVIEW_ACTIONS,
    PLAN_REVIEW_ACTION_TO_STATUS,
    find_prohibited_language,
)
from app.db import models


class PlanReviewActionError(Exception):
    """Raised when a requested plan review action is not allowed."""

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
            audit_event_id=f"audit_plan_{uuid.uuid4().hex[:12]}",
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


def list_plan_consistency_review_actions(
    db: Session,
    project_id: str,
    plan_finding_id: str | None = None,
) -> list[models.PlanConsistencyReviewAction]:
    """Return review actions for a project, optionally for one finding."""

    stmt = select(models.PlanConsistencyReviewAction).where(
        models.PlanConsistencyReviewAction.project_id == project_id
    )
    if plan_finding_id is not None:
        stmt = stmt.where(
            models.PlanConsistencyReviewAction.plan_finding_id == plan_finding_id
        )
    stmt = stmt.order_by(models.PlanConsistencyReviewAction.created_at)
    return list(db.scalars(stmt).all())


def create_plan_consistency_review_action(
    db: Session,
    *,
    plan_finding_id: str,
    action: str,
    reviewer_name: str,
    reviewer_note: str,
) -> tuple[
    models.PlanConsistencyReviewAction, models.PlanConsistencyFinding
]:
    """Validate and persist a review action on a plan consistency finding."""

    finding = db.scalars(
        select(models.PlanConsistencyFinding).where(
            models.PlanConsistencyFinding.plan_finding_id == plan_finding_id
        )
    ).first()
    if finding is None:
        raise PlanReviewActionError(
            "Plan consistency finding not found.", status_code=404
        )

    if action not in ALLOWED_PLAN_REVIEW_ACTIONS:
        raise PlanReviewActionError(
            f"Unknown plan review action '{action}'.", status_code=422
        )
    if not reviewer_name or not reviewer_name.strip():
        raise PlanReviewActionError("reviewer_name is required.", status_code=422)
    if not reviewer_note or not reviewer_note.strip():
        raise PlanReviewActionError("reviewer_note is required.", status_code=422)
    if find_prohibited_language(reviewer_note):
        raise PlanReviewActionError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    previous_status = finding.status
    new_status = PLAN_REVIEW_ACTION_TO_STATUS[action]
    finding.status = new_status

    review_action_id = f"pra_{uuid.uuid4().hex[:12]}"
    record = models.PlanConsistencyReviewAction(
        review_action_id=review_action_id,
        plan_finding_id=plan_finding_id,
        project_id=finding.project_id,
        reviewer_name=reviewer_name.strip(),
        action=action,
        reviewer_note=reviewer_note.strip(),
        previous_status=previous_status,
        new_status=new_status,
    )
    db.add(record)

    _audit(
        db,
        project_id=finding.project_id,
        event_type="plan_consistency_review_action_recorded",
        related_entity_type="plan_consistency_review_action",
        related_entity_id=review_action_id,
        description=(
            f"Plan consistency review action '{action}' recorded by "
            f"{reviewer_name}."
        ),
        metadata={
            "review_action_id": review_action_id,
            "plan_finding_id": plan_finding_id,
            "action": action,
            "reviewer_name": reviewer_name,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )
    _audit(
        db,
        project_id=finding.project_id,
        event_type="plan_finding_status_updated",
        related_entity_type="plan_consistency_finding",
        related_entity_id=plan_finding_id,
        description=(
            f"Plan consistency finding status updated from {previous_status} "
            f"to {new_status}."
        ),
        metadata={
            "review_action_id": review_action_id,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )

    db.commit()
    db.refresh(record)
    db.refresh(finding)
    return record, finding
