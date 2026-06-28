"""Hotspot API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.hotspot import HotspotRead
from app.services import hotspot_service, project_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
)

router = APIRouter(tags=["hotspots"])


@router.get(
    "/projects/{project_id}/hotspots", response_model=list[HotspotRead]
)
def list_hotspots(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[HotspotRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return hotspot_service.list_hotspots(db, project_id)
