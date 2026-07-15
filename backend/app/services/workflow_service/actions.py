"""Reviewer status transitions and note recording on workflow items."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_WORKFLOW_STATUSES,
    WORKFLOW_STATUS_TO_ACTION,
    find_prohibited_language,
)
from app.db import models

from ._common import _audit, _now, _record_action
from .errors import WorkflowError
from .reads import get_workflow_item_record


def update_workflow_item_status(
    db: Session,
    *,
    workflow_item_id: str,
    new_status: str,
    reviewer_note: str | None = None,
    reviewer_name: str | None = None,
    target_date: str | None = None,
) -> models.WorkflowItem:
    """Validate and apply a board status transition to a workflow item.

    Writes a workflow_action of the mapped action type and a
    workflow_item_status_updated audit event.
    """

    item = get_workflow_item_record(db, workflow_item_id)
    if item is None:
        raise WorkflowError("Workflow item not found.", status_code=404)
    if new_status not in ALLOWED_WORKFLOW_STATUSES:
        raise WorkflowError(
            f"Unknown workflow status '{new_status}'.", status_code=422
        )
    if new_status not in WORKFLOW_STATUS_TO_ACTION:
        # draft is the seeded status and is not a manual transition target.
        raise WorkflowError(
            f"Status '{new_status}' is not a valid manual transition.",
            status_code=422,
        )
    note = (reviewer_note or "").strip()
    if find_prohibited_language(note):
        raise WorkflowError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    action_type = WORKFLOW_STATUS_TO_ACTION[new_status]
    previous_status = item.status
    item.status = new_status
    if note:
        item.reviewer_note = note
    if target_date is not None:
        item.target_date = target_date
    item.updated_at = _now()

    _record_action(
        db,
        item=item,
        action_type=action_type,
        previous_status=previous_status,
        new_status=new_status,
        reviewer_note=note or "Status updated by reviewer.",
        reviewer_name=(reviewer_name or "reviewer").strip(),
    )
    _audit(
        db,
        project_id=item.project_id,
        event_type="workflow_item_status_updated",
        related_entity_type="workflow_item",
        related_entity_id=item.workflow_item_id,
        description=(
            f"Workflow item status updated from {previous_status} to "
            f"{new_status} via {action_type}."
        ),
        actor_type="reviewer",
        metadata={
            "workflow_item_id": item.workflow_item_id,
            "action_type": action_type,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def add_workflow_note(
    db: Session,
    *,
    workflow_item_id: str,
    reviewer_note: str,
    reviewer_name: str,
) -> models.WorkflowItem:
    """Record a reviewer note on a workflow item without changing its status.

    Writes a note_added workflow action and a workflow_note_added audit event.
    """

    item = get_workflow_item_record(db, workflow_item_id)
    if item is None:
        raise WorkflowError("Workflow item not found.", status_code=404)
    note = (reviewer_note or "").strip()
    if not note:
        raise WorkflowError("reviewer_note is required.", status_code=422)
    if not reviewer_name or not reviewer_name.strip():
        raise WorkflowError("reviewer_name is required.", status_code=422)
    if find_prohibited_language(note):
        raise WorkflowError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    item.reviewer_note = note
    item.updated_at = _now()
    _record_action(
        db,
        item=item,
        action_type="note_added",
        previous_status=item.status,
        new_status=item.status,
        reviewer_note=note,
        reviewer_name=reviewer_name.strip(),
    )
    _audit(
        db,
        project_id=item.project_id,
        event_type="workflow_note_added",
        related_entity_type="workflow_item",
        related_entity_id=item.workflow_item_id,
        description=f"Reviewer note added by {reviewer_name.strip()}.",
        actor_type="reviewer",
        metadata={"workflow_item_id": item.workflow_item_id},
    )
    db.commit()
    db.refresh(item)
    return item
