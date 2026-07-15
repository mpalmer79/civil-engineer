"""Read accessors, item detail projection, and board summaries.

Several read entry points have an intentional audit side effect so the decision
history reflects reviewer access.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import ALLOWED_FOLLOW_UP_STATUSES
from app.db import models
from app.services import review_packet_service

from ._common import BOARD_NOTE, HANDOFF_NOTE, _audit


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
