"""Shared helpers, constants, and routing tables for the workflow service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import models

INITIAL_STATUS = "draft"

# Maps a packet section type to the reviewer role that normally works the item
# on the board. These are descriptive routing roles, not engineering authority.
SECTION_TO_ROLE: dict[str, str] = {
    "executive_summary": "review_coordinator",
    "document_checklist": "intake_reviewer",
    "plan_sheet_cad": "plan_reviewer",
    "sheet_hotspots": "plan_reviewer",
    "plan_consistency": "plan_reviewer",
    "human_review_actions": "review_coordinator",
    "traceability": "review_coordinator",
    "limitations": "review_coordinator",
}
DEFAULT_ROLE = "review_coordinator"

BOARD_NOTE = (
    "This board organizes review-support items for human reviewers. It does "
    "not approve plans, certify compliance, verify CAD, validate a design, or "
    "make final engineering decisions."
)

HANDOFF_NOTE = (
    "Ready for handoff means the organized review-support evidence is ready to "
    "hand to a licensed Professional Engineer. It is not an approval, "
    "certification, or final engineering decision."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    actor_type: str = "system",
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_wf_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type=actor_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def _record_action(
    db: Session,
    *,
    item: models.WorkflowItem,
    action_type: str,
    previous_status: str,
    new_status: str,
    reviewer_note: str,
    reviewer_name: str,
) -> models.WorkflowAction:
    action = models.WorkflowAction(
        action_id=f"wf_act_{_short()}",
        workflow_item_id=item.workflow_item_id,
        project_id=item.project_id,
        action_type=action_type,
        previous_status=previous_status,
        new_status=new_status,
        reviewer_note=reviewer_note,
        reviewer_name=reviewer_name,
    )
    db.add(action)
    return action
