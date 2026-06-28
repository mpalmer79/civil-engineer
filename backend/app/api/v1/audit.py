"""Audit event API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.audit import AuditEventRead
from app.services import audit_service, project_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
)

router = APIRouter(tags=["audit"])


@router.get(
    "/projects/{project_id}/audit-events", response_model=list[AuditEventRead]
)
def list_audit_events(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[AuditEventRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return audit_service.list_audit_events(db, project_id)
