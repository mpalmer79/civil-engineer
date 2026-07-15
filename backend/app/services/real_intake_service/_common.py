"""Shared identity, id, actor, audit, and project-lookup helpers.

These helpers are reused across the intake package submodules and by several
sibling services. Keeping them in one place preserves a single source of truth
for the demo reviewer identity, id generation, and durable audit events.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import models
from app.services.real_intake_service.errors import IntakeError

# Fixed identity for the Sprint 1 demo reviewer. Real authentication will
# replace this placeholder; it grants no access and is attribution only.
DEMO_ACTOR_ID = "actor_demo_reviewer"
DEMO_ACTOR_NAME = "Demo Reviewer"

REVIEW_SUPPORT_NOTE = (
    "Review-support record only. It does not approve plans, certify compliance, "
    "verify CAD, validate design, or replace a licensed Professional Engineer. "
    "It requires human review."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Actor and audit helpers
# ---------------------------------------------------------------------------


def ensure_demo_actor(db: Session) -> models.Actor:
    """Create the Sprint 1 demo reviewer identity if it does not exist."""

    actor = db.get(models.Actor, DEMO_ACTOR_ID)
    if actor is None:
        actor = models.Actor(
            actor_id=DEMO_ACTOR_ID,
            display_name=DEMO_ACTOR_NAME,
            actor_type="reviewer",
            organization_name="Municipal Review Team (demo)",
            role_label="Stormwater Reviewer (demo)",
            created_at=_now(),
        )
        db.add(actor)
    return actor


def record_audit_event(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    actor_type: str = "reviewer",
    actor_id: str | None = DEMO_ACTOR_ID,
    actor_display_name: str | None = DEMO_ACTOR_NAME,
    metadata: dict | None = None,
    request_id: str | None = None,
    user_id: str | None = None,
    user_email: str | None = None,
    organization_id: str | None = None,
    access_level: str | None = None,
) -> models.AuditEvent:
    """Create a durable audit event for a real action.

    Never stores secrets, tokens, passwords, password hashes, raw IP addresses,
    or raw user agents. event_metadata holds only non-sensitive structured
    context. When a signed-in user takes the action (Sprint 5), the user and
    organization identity is recorded for real attribution.
    """

    event = models.AuditEvent(
        audit_event_id=f"audit_{_short()}",
        project_id=project_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_display_name=actor_display_name,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        description=description,
        timestamp=_now(),
        event_metadata=metadata or {},
        request_id=request_id,
        user_id=user_id,
        user_email=user_email,
        organization_id=organization_id,
        access_level=access_level,
    )
    db.add(event)
    return event


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise IntakeError("Project not found.", status_code=404)
    return project
