"""Follow-up request handling for workflow items."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.safety import find_prohibited_language
from app.db import models

from ._common import _audit, _now, _record_action, _short
from .errors import WorkflowError
from .reads import get_workflow_item_record


def create_follow_up_request(
    db: Session,
    *,
    workflow_item_id: str,
    requested_from: str,
    request_reason: str,
    requested_information: str,
    reviewer_name: str,
    target_date: str | None = None,
) -> models.WorkflowFollowUpRequest:
    """Open a follow-up request against a workflow item.

    Recording a follow-up request also moves the item to needs_follow_up and
    writes a follow_up_requested workflow action plus a
    workflow_follow_up_requested audit event.
    """

    item = get_workflow_item_record(db, workflow_item_id)
    if item is None:
        raise WorkflowError("Workflow item not found.", status_code=404)
    requested_from = (requested_from or "").strip()
    request_reason = (request_reason or "").strip()
    requested_information = (requested_information or "").strip()
    reviewer_name = (reviewer_name or "").strip()
    if not requested_from:
        raise WorkflowError("requested_from is required.", status_code=422)
    if not request_reason:
        raise WorkflowError("request_reason is required.", status_code=422)
    if not requested_information:
        raise WorkflowError(
            "requested_information is required.", status_code=422
        )
    if not reviewer_name:
        raise WorkflowError("reviewer_name is required.", status_code=422)
    for text in (request_reason, requested_information):
        if find_prohibited_language(text):
            raise WorkflowError(
                "Follow-up request contains prohibited final-decision wording.",
                status_code=422,
            )

    follow_up = models.WorkflowFollowUpRequest(
        follow_up_id=f"wf_fu_{_short()}",
        workflow_item_id=item.workflow_item_id,
        project_id=item.project_id,
        requested_from=requested_from,
        request_reason=request_reason,
        requested_information=requested_information,
        target_date=target_date,
        status="open",
        reviewer_name=reviewer_name,
    )
    db.add(follow_up)

    previous_status = item.status
    item.status = "needs_follow_up"
    if target_date is not None:
        item.target_date = target_date
    item.updated_at = _now()
    _record_action(
        db,
        item=item,
        action_type="follow_up_requested",
        previous_status=previous_status,
        new_status="needs_follow_up",
        reviewer_note=request_reason,
        reviewer_name=reviewer_name,
    )
    _audit(
        db,
        project_id=item.project_id,
        event_type="workflow_follow_up_requested",
        related_entity_type="workflow_item",
        related_entity_id=item.workflow_item_id,
        description=(
            f"Follow-up requested from {requested_from} by {reviewer_name}."
        ),
        actor_type="reviewer",
        metadata={
            "workflow_item_id": item.workflow_item_id,
            "follow_up_id": follow_up.follow_up_id,
            "requested_from": requested_from,
        },
    )
    db.commit()
    db.refresh(follow_up)
    return follow_up
