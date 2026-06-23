"""Pydantic schemas for CAD-aware metadata.

CAD-aware metadata is seeded, not extracted from DWG or DXF files. It describes
civil features for review support and does not verify any drawing as correct.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CadMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cad_metadata_id: str
    project_id: str
    sheet_id: str | None
    source_type: str
    entity_type: str
    entity_label: str
    layer_name: str | None
    discipline: str
    related_document_id: str | None
    related_checklist_item_id: str | None
    related_finding_id: str | None
    notes: str | None
    created_at: datetime
