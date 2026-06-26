"""Pydantic schemas for audit events."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_event_id: str
    project_id: str
    event_type: str
    actor_type: str
    related_entity_type: str
    related_entity_id: str
    description: str
    timestamp: datetime
    event_metadata: dict = {}
    # Production foundation actor attribution and request context. Raw IP and
    # user agent are never stored; only optional hashes may be present.
    actor_id: str | None = None
    actor_display_name: str | None = None
    request_id: str | None = None
    # Sprint 5 authenticated user attribution. Present when a signed-in user took
    # the action. Never includes tokens, passwords, or password hashes.
    user_id: str | None = None
    user_email: str | None = None
    organization_id: str | None = None
    access_level: str | None = None
