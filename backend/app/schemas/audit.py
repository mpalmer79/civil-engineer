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
