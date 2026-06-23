"""Hotspot API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.hotspot import HotspotRead
from app.services import hotspot_service, project_service

router = APIRouter(tags=["hotspots"])


@router.get(
    "/projects/{project_id}/hotspots", response_model=list[HotspotRead]
)
def list_hotspots(
    project_id: str, db: Session = Depends(get_db)
) -> list[HotspotRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return hotspot_service.list_hotspots(db, project_id)
