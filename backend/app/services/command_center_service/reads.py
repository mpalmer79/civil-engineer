"""Command center read endpoints, reviewer notes, next steps, and the combined view."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import ALLOWED_ATTENTION_ITEM_STATUSES
from app.db import models
from app.services.command_center_service._common import (
    LIMITATIONS_NOTE,
    ROUTE_WORKFLOW,
    _attention_for,
    _audit,
    _metrics_for,
    _readiness_for,
    _require_project,
    _short,
    _SEVERITY_RANK,
    get_latest_snapshot_record,
)
from app.services.command_center_service.errors import CommandCenterError
from app.services.command_center_service.metrics import _module_links_payload
from app.services.command_center_service.queues import (
    _ensure_snapshot,
    generate_command_center_snapshot,
)


def get_latest_command_center_snapshot(
    db: Session, project_id: str
) -> models.ProjectCommandCenterSnapshot | None:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_latest_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Latest command center snapshot viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return snapshot


def get_reviewer_attention_items(
    db: Session,
    project_id: str,
    *,
    status: str | None = None,
    severity: str | None = None,
    source_module: str | None = None,
    attention_type: str | None = None,
) -> list:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    items = _attention_for(
        db,
        snapshot.snapshot_id,
        status=status,
        severity=severity,
        source_module=source_module,
        attention_type=attention_type,
    )
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_attention_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center attention items viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id, "count": len(items)},
    )
    db.commit()
    return items


def update_attention_item_status(
    db: Session,
    attention_item_id: str,
    *,
    status: str,
    reviewer_note: str | None = None,
    reviewer_name: str = "reviewer",
) -> models.ReviewerAttentionItem:
    item = db.scalars(
        select(models.ReviewerAttentionItem).where(
            models.ReviewerAttentionItem.attention_item_id == attention_item_id
        )
    ).first()
    if item is None:
        raise CommandCenterError("Attention item not found.", status_code=404)
    if status not in ALLOWED_ATTENTION_ITEM_STATUSES:
        raise CommandCenterError(
            f"Invalid attention item status '{status}'.", status_code=422
        )
    previous = item.status
    item.status = status
    _audit(
        db,
        project_id=item.project_id,
        event_type="command_center_attention_status_changed",
        related_entity_type="reviewer_attention_item",
        related_entity_id=attention_item_id,
        description=(
            f"Attention item status changed from {previous} to {status} by "
            f"{reviewer_name}."
            + (f" Note: {reviewer_note}" if reviewer_note else "")
        ),
        metadata={"previous_status": previous, "new_status": status},
    )
    db.commit()
    db.refresh(item)
    return item


def get_review_readiness_checks(db: Session, project_id: str) -> list:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    checks = _readiness_for(db, snapshot.snapshot_id)
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_readiness_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center readiness checks viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return checks


def add_dashboard_reviewer_note(
    db: Session,
    project_id: str,
    *,
    note_text: str,
    reviewer_name: str = "reviewer",
    snapshot_id: str | None = None,
    source_context: str | None = None,
) -> models.DashboardReviewerNote:
    _require_project(db, project_id)
    if snapshot_id is None:
        latest = get_latest_snapshot_record(db, project_id)
        snapshot_id = latest.snapshot_id if latest else None
    note = models.DashboardReviewerNote(
        note_id=f"note_{_short()}",
        project_id=project_id,
        snapshot_id=snapshot_id,
        note_text=note_text,
        reviewer_name=reviewer_name,
        source_context=source_context,
        requires_human_review=True,
    )
    db.add(note)
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_note_added",
        related_entity_type="dashboard_reviewer_note",
        related_entity_id=note.note_id,
        description="Dashboard reviewer note added.",
        metadata={"note_id": note.note_id},
    )
    db.commit()
    db.refresh(note)
    return note


def get_dashboard_reviewer_notes(db: Session, project_id: str) -> list:
    _require_project(db, project_id)
    notes = list(
        db.scalars(
            select(models.DashboardReviewerNote)
            .where(models.DashboardReviewerNote.project_id == project_id)
            .order_by(models.DashboardReviewerNote.created_at.desc())
        ).all()
    )
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_notes_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Dashboard reviewer notes viewed.",
        metadata={"note_count": len(notes)},
    )
    db.commit()
    return notes


def get_reviewer_next_steps(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    open_items = _attention_for(db, snapshot.snapshot_id, status="open")
    # One step per attention type, highest severity first.
    by_type: dict[str, models.ReviewerAttentionItem] = {}
    for item in open_items:
        current = by_type.get(item.attention_type)
        if current is None or _SEVERITY_RANK.get(item.severity, 0) > _SEVERITY_RANK.get(
            current.severity, 0
        ):
            by_type[item.attention_type] = item
    ordered = sorted(
        by_type.values(),
        key=lambda i: _SEVERITY_RANK.get(i.severity, 0),
        reverse=True,
    )
    steps = [
        {
            "title": item.title,
            "detail": item.recommended_next_step,
            "severity": item.severity,
            "target_route": item.target_route,
            "source_module": item.source_module,
        }
        for item in ordered[:6]
    ]
    if not steps:
        steps = [
            {
                "title": "Route organized evidence for human review",
                "detail": (
                    "No open attention items. A licensed Professional Engineer "
                    "review is still required before any final decision."
                ),
                "severity": "info",
                "target_route": ROUTE_WORKFLOW,
                "source_module": "human_review",
            }
        ]
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_next_steps_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center next steps viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return {
        "project_id": project_id,
        "snapshot_id": snapshot.snapshot_id,
        "steps": steps,
        "note": (
            "Recommended review-support steps. None of these approves, certifies, "
            "or finalizes the work."
        ),
    }


def get_project_command_center(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    metrics = _metrics_for(db, snapshot.snapshot_id)
    attention = _attention_for(db, snapshot.snapshot_id, status="open")
    timeline = list(
        db.scalars(
            select(models.ProjectTimelineEvent)
            .where(models.ProjectTimelineEvent.project_id == project_id)
            .order_by(models.ProjectTimelineEvent.event_time)
        ).all()
    )
    readiness = _readiness_for(db, snapshot.snapshot_id)
    notes = list(
        db.scalars(
            select(models.DashboardReviewerNote)
            .where(models.DashboardReviewerNote.project_id == project_id)
            .order_by(models.DashboardReviewerNote.created_at.desc())
        ).all()
    )

    # Next steps and module links assembled inline (no extra audit writes here).
    open_items = attention
    by_type: dict[str, models.ReviewerAttentionItem] = {}
    for item in open_items:
        current = by_type.get(item.attention_type)
        if current is None or _SEVERITY_RANK.get(item.severity, 0) > _SEVERITY_RANK.get(
            current.severity, 0
        ):
            by_type[item.attention_type] = item
    ordered = sorted(
        by_type.values(),
        key=lambda i: _SEVERITY_RANK.get(i.severity, 0),
        reverse=True,
    )
    steps = [
        {
            "title": item.title,
            "detail": item.recommended_next_step,
            "severity": item.severity,
            "target_route": item.target_route,
            "source_module": item.source_module,
        }
        for item in ordered[:6]
    ] or [
        {
            "title": "Route organized evidence for human review",
            "detail": (
                "No open attention items. A licensed Professional Engineer review "
                "is still required before any final decision."
            ),
            "severity": "info",
            "target_route": ROUTE_WORKFLOW,
            "source_module": "human_review",
        }
    ]
    next_steps = {
        "project_id": project_id,
        "snapshot_id": snapshot.snapshot_id,
        "steps": steps,
        "note": (
            "Recommended review-support steps. None of these approves, certifies, "
            "or finalizes the work."
        ),
    }
    module_links = _module_links_payload(db, project_id)

    _audit(
        db,
        project_id=project_id,
        event_type="command_center_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Project command center viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return {
        "snapshot": snapshot,
        "health_metrics": metrics,
        "attention_items": attention,
        "timeline": timeline,
        "readiness_checks": readiness,
        "next_steps": next_steps,
        "module_links": module_links,
        "reviewer_notes": notes,
        "limitations_note": LIMITATIONS_NOTE,
    }


def ensure_command_center(db: Session, project_id: str) -> None:
    """Generate an initial command center snapshot once if none exists."""

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.ProjectCommandCenterSnapshot)
        .filter(models.ProjectCommandCenterSnapshot.project_id == project_id)
        .first()
    )
    if existing is None:
        generate_command_center_snapshot(db, project_id)
