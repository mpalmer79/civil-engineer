"""CAD-aware metadata API routes for the Phase 6 foundation.

These endpoints expose seeded CAD-aware feature metadata. The metadata is
seeded, not extracted from DWG or DXF files, and does not verify any drawing as
correct.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.cad_metadata import CadMetadataRead
from app.services import cad_metadata_service, project_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
)

router = APIRouter(tags=["cad-metadata"])


@router.get(
    "/projects/{project_id}/cad-metadata",
    response_model=list[CadMetadataRead],
)
def list_cad_metadata(
    project_id: str,
    entity_type: str | None = None,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadMetadataRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return cad_metadata_service.list_cad_metadata(db, project_id, entity_type)


@router.get(
    "/cad-metadata/{cad_metadata_id}",
    response_model=CadMetadataRead,
)
def get_cad_metadata(
    cad_metadata_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadMetadataRead:
    record = cad_metadata_service.get_cad_metadata(db, cad_metadata_id)
    if record is None:
        raise HTTPException(status_code=404, detail="CAD metadata not found")
    # Resolve the owning project so a raw metadata id cannot bypass access.
    require_project_read(db, record.project_id, user)
    return record
