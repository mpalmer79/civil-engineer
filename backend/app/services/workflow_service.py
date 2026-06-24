"""Reviewer workflow board service for Phase 9.

This service promotes the review-support items in the latest review packet into
an operational workflow board. A human reviewer can triage each item, request
follow-up or more information, record reviewer notes, mark items reviewer
checked or excluded, and finally mark items ready for handoff to a licensed
Professional Engineer.

The workflow board organizes review-support work. It does not approve plans,
certify compliance, stamp drawings, verify CAD, validate a design, or make
final engineering decisions. There is no action called approve. Handoff means
handing the organized evidence to a human reviewer, not issuing a decision.

Read side effects: get_workflow_item, get_workflow_item_history,
get_workflow_board_summary, and get_ready_for_handoff_summary each write an
audit event recording the access, so the decision history shows reviewer
activity.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_FOLLOW_UP_STATUSES,
    ALLOWED_WORKFLOW_STATUSES,
    WORKFLOW_STATUS_TO_ACTION,
    find_prohibited_language,
)
from app.db import models
from app.services import review_packet_service

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


class WorkflowError(Exception):
    """Raised when a workflow board operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


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


def _delete_existing(db: Session, project_id: str) -> None:
    item_ids = [
        i.workflow_item_id
        for i in db.scalars(
            select(models.WorkflowItem).where(
                models.WorkflowItem.project_id == project_id
            )
        ).all()
    ]
    if not item_ids:
        return
    for model in (
        models.WorkflowFollowUpRequest,
        models.WorkflowAction,
    ):
        db.query(model).filter(
            model.workflow_item_id.in_(item_ids)
        ).delete(synchronize_session=False)
    db.query(models.WorkflowItem).filter(
        models.WorkflowItem.project_id == project_id
    ).delete(synchronize_session=False)
    db.commit()


def generate_workflow_items_from_review_packet(
    db: Session, project_id: str
) -> list[models.WorkflowItem]:
    """Generate a fresh workflow board for a project from its latest packet.

    Idempotent: existing workflow items, actions, and follow-up requests for the
    project are removed and a new board is built from the most recent review
    packet. Only packet items that require human review become workflow items,
    since informational summary, traceability, and limitations items do not need
    operational tracking. Writes a workflow_board_generated audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise WorkflowError("Project not found.", status_code=404)

    packets = review_packet_service.list_review_packets(db, project_id)
    if not packets:
        # Ensure a packet exists so the board has source items to promote.
        review_packet_service.generate_review_packet(db, project_id)
        packets = review_packet_service.list_review_packets(db, project_id)
    packet = packets[0]
    detail = review_packet_service.assemble_packet_detail(db, packet)

    _delete_existing(db, project_id)

    created: list[models.WorkflowItem] = []
    for section in detail["sections"]:
        section_type = section["section_type"]
        role = SECTION_TO_ROLE.get(section_type, DEFAULT_ROLE)
        for item in section["items"]:
            if not item["requires_human_review"]:
                continue
            evidence_types = sorted(
                {link.evidence_type for link in item["evidence_links"]}
            )
            workflow_item = models.WorkflowItem(
                workflow_item_id=f"wfi_{_short()}",
                project_id=project_id,
                packet_id=packet.packet_id,
                packet_item_id=item["item_id"],
                title=item["title"],
                description=item["description"],
                source_type=item["source_type"],
                source_id=item["source_id"],
                severity=item["severity"],
                status=INITIAL_STATUS,
                assigned_role=role,
                reviewer_note=None,
                target_date=None,
                section_type=section_type,
                evidence_types=evidence_types,
                requires_human_review=True,
            )
            db.add(workflow_item)
            created.append(workflow_item)

    _audit(
        db,
        project_id=project_id,
        event_type="workflow_board_generated",
        related_entity_type="workflow_board",
        related_entity_id=project_id,
        description=(
            f"Reviewer workflow board generated with {len(created)} items from "
            f"packet {packet.packet_id}."
        ),
        metadata={
            "packet_id": packet.packet_id,
            "item_count": len(created),
        },
    )
    db.commit()
    for item in created:
        db.refresh(item)
    return created


def ensure_workflow_board(db: Session, project_id: str) -> None:
    """Generate a workflow board once if none exists for the project.

    Used at startup so the read endpoints and frontend have a board without a
    manual generate call. Gated on no workflow items existing, so it does not
    regenerate on every restart.
    """

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.WorkflowItem)
        .filter(models.WorkflowItem.project_id == project_id)
        .first()
    )
    if existing is None:
        generate_workflow_items_from_review_packet(db, project_id)


def get_workflow_item_record(
    db: Session, workflow_item_id: str
) -> models.WorkflowItem | None:
    return db.scalars(
        select(models.WorkflowItem).where(
            models.WorkflowItem.workflow_item_id == workflow_item_id
        )
    ).first()


def list_workflow_items(
    db: Session,
    project_id: str,
    *,
    status: str | None = None,
    severity: str | None = None,
    section_type: str | None = None,
    assigned_role: str | None = None,
    source_type: str | None = None,
) -> list[models.WorkflowItem]:
    """Return workflow items for a project, optionally filtered."""

    stmt = select(models.WorkflowItem).where(
        models.WorkflowItem.project_id == project_id
    )
    if status is not None:
        stmt = stmt.where(models.WorkflowItem.status == status)
    if severity is not None:
        stmt = stmt.where(models.WorkflowItem.severity == severity)
    if section_type is not None:
        stmt = stmt.where(models.WorkflowItem.section_type == section_type)
    if assigned_role is not None:
        stmt = stmt.where(models.WorkflowItem.assigned_role == assigned_role)
    if source_type is not None:
        stmt = stmt.where(models.WorkflowItem.source_type == source_type)
    stmt = stmt.order_by(models.WorkflowItem.created_at)
    return list(db.scalars(stmt).all())


def list_workflow_actions(
    db: Session, workflow_item_id: str
) -> list[models.WorkflowAction]:
    stmt = (
        select(models.WorkflowAction)
        .where(models.WorkflowAction.workflow_item_id == workflow_item_id)
        .order_by(models.WorkflowAction.created_at)
    )
    return list(db.scalars(stmt).all())


def list_follow_up_requests(
    db: Session, workflow_item_id: str
) -> list[models.WorkflowFollowUpRequest]:
    stmt = (
        select(models.WorkflowFollowUpRequest)
        .where(
            models.WorkflowFollowUpRequest.workflow_item_id == workflow_item_id
        )
        .order_by(models.WorkflowFollowUpRequest.created_at)
    )
    return list(db.scalars(stmt).all())


def _evidence_links_for_item(
    db: Session, item: models.WorkflowItem
) -> list[models.ReviewPacketEvidenceLink]:
    if not item.packet_item_id:
        return []
    return review_packet_service.list_evidence_links_for_item(
        db, item.packet_item_id
    )


def _assemble_item_detail(db: Session, item: models.WorkflowItem) -> dict:
    return {
        "workflow_item_id": item.workflow_item_id,
        "project_id": item.project_id,
        "packet_id": item.packet_id,
        "packet_item_id": item.packet_item_id,
        "title": item.title,
        "description": item.description,
        "source_type": item.source_type,
        "source_id": item.source_id,
        "severity": item.severity,
        "status": item.status,
        "assigned_role": item.assigned_role,
        "reviewer_note": item.reviewer_note,
        "target_date": item.target_date,
        "section_type": item.section_type,
        "evidence_types": item.evidence_types or [],
        "requires_human_review": item.requires_human_review,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "evidence_links": _evidence_links_for_item(db, item),
        "follow_ups": list_follow_up_requests(db, item.workflow_item_id),
        "actions": list_workflow_actions(db, item.workflow_item_id),
    }


def get_workflow_item(db: Session, workflow_item_id: str) -> dict | None:
    """Return a workflow item detail and record that it was viewed.

    Read side effect: writes a workflow_item_viewed audit event.
    """

    item = get_workflow_item_record(db, workflow_item_id)
    if item is None:
        return None
    _audit(
        db,
        project_id=item.project_id,
        event_type="workflow_item_viewed",
        related_entity_type="workflow_item",
        related_entity_id=workflow_item_id,
        description="Workflow item viewed.",
        actor_type="reviewer",
        metadata={"workflow_item_id": workflow_item_id},
    )
    db.commit()
    return _assemble_item_detail(db, item)


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


def get_workflow_item_history(
    db: Session, workflow_item_id: str
) -> dict | None:
    """Return the full action and follow-up history for a workflow item.

    Read side effect: writes a workflow_item_history_requested audit event.
    """

    item = get_workflow_item_record(db, workflow_item_id)
    if item is None:
        return None
    actions = list_workflow_actions(db, workflow_item_id)
    follow_ups = list_follow_up_requests(db, workflow_item_id)
    _audit(
        db,
        project_id=item.project_id,
        event_type="workflow_item_history_requested",
        related_entity_type="workflow_item",
        related_entity_id=workflow_item_id,
        description="Workflow item history requested.",
        actor_type="reviewer",
        metadata={
            "workflow_item_id": workflow_item_id,
            "action_count": len(actions),
            "follow_up_count": len(follow_ups),
        },
    )
    db.commit()
    return {
        "workflow_item_id": workflow_item_id,
        "project_id": item.project_id,
        "actions": actions,
        "follow_ups": follow_ups,
        "note": (
            "This is the recorded reviewer activity for the item. It is "
            "review-support history, not a final engineering decision."
        ),
    }


def _open_follow_up_count(db: Session, project_id: str) -> int:
    open_statuses = ALLOWED_FOLLOW_UP_STATUSES - {"closed_without_decision"}
    return (
        db.query(models.WorkflowFollowUpRequest)
        .filter(
            models.WorkflowFollowUpRequest.project_id == project_id,
            models.WorkflowFollowUpRequest.status.in_(open_statuses),
        )
        .count()
    )


def get_workflow_board_summary(
    db: Session, project_id: str
) -> dict | None:
    """Return board level counts for a project.

    Read side effect: writes a workflow_board_summary_requested audit event.
    """

    if db.get(models.Project, project_id) is None:
        return None
    items = list_workflow_items(db, project_id)

    by_status: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_section: dict[str, int] = {}
    by_role: dict[str, int] = {}
    for item in items:
        by_status[item.status] = by_status.get(item.status, 0) + 1
        by_severity[item.severity] = by_severity.get(item.severity, 0) + 1
        by_section[item.section_type] = by_section.get(item.section_type, 0) + 1
        by_role[item.assigned_role] = by_role.get(item.assigned_role, 0) + 1

    ready = by_status.get("ready_for_handoff", 0)
    _audit(
        db,
        project_id=project_id,
        event_type="workflow_board_summary_requested",
        related_entity_type="workflow_board",
        related_entity_id=project_id,
        description="Workflow board summary requested.",
        actor_type="reviewer",
        metadata={"item_count": len(items)},
    )
    db.commit()
    return {
        "project_id": project_id,
        "total_items": len(items),
        "items_by_status": by_status,
        "items_by_severity": by_severity,
        "items_by_section_type": by_section,
        "items_by_assigned_role": by_role,
        "items_requiring_human_review": len(
            [i for i in items if i.requires_human_review]
        ),
        "open_follow_up_count": _open_follow_up_count(db, project_id),
        "ready_for_handoff_count": ready,
        "note": BOARD_NOTE,
    }


def get_ready_for_handoff_summary(
    db: Session, project_id: str
) -> dict | None:
    """Return the items marked ready for handoff and outstanding follow-ups.

    Read side effect: writes a workflow_ready_for_handoff_requested audit event.
    """

    if db.get(models.Project, project_id) is None:
        return None
    all_items = list_workflow_items(db, project_id)
    ready_items = [i for i in all_items if i.status == "ready_for_handoff"]

    _audit(
        db,
        project_id=project_id,
        event_type="workflow_ready_for_handoff_requested",
        related_entity_type="workflow_board",
        related_entity_id=project_id,
        description="Workflow ready-for-handoff summary requested.",
        actor_type="reviewer",
        metadata={
            "ready_count": len(ready_items),
            "total_items": len(all_items),
        },
    )
    db.commit()
    return {
        "project_id": project_id,
        "total_items": len(all_items),
        "ready_count": len(ready_items),
        "outstanding_follow_up_count": _open_follow_up_count(db, project_id),
        "items": ready_items,
        "note": HANDOFF_NOTE,
    }
