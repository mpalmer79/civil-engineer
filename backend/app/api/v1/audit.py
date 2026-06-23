"""Audit event API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.audit import AuditEventRead
from app.services import audit_service, project_service

router = APIRouter(tags=["audit"])


@router.get(
    "/projects/{project_id}/audit-events", response_model=list[AuditEventRead]
)
def list_audit_events(
    project_id: str, db: Session = Depends(get_db)
) -> list[AuditEventRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return audit_service.list_audit_events(db, project_id)
