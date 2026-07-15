"""Command center project timeline (activity) projection."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.command_center_service._common import _audit, _require_project
from app.services.command_center_service.queues import _ensure_snapshot


def get_project_timeline(db: Session, project_id: str) -> list:
    _require_project(db, project_id)
    _ensure_snapshot(db, project_id)
    events = list(
        db.scalars(
            select(models.ProjectTimelineEvent)
            .where(models.ProjectTimelineEvent.project_id == project_id)
            .order_by(models.ProjectTimelineEvent.event_time)
        ).all()
    )
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_timeline_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Command center timeline viewed.",
        metadata={"event_count": len(events)},
    )
    db.commit()
    return events
