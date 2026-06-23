"""CAD-aware metadata read service.

Provides read access to the seeded CAD-aware feature metadata for a project.
This metadata is seeded, not extracted from real CAD files. It is a future-ready
abstraction so later phases can populate the same shape from DXF exports or an
Autodesk viewer. It is not CAD verified.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def list_cad_metadata(
    db: Session,
    project_id: str,
    *,
    entity_type: str | None = None,
    sheet_id: str | None = None,
) -> list[models.CADMetadata]:
    stmt = select(models.CADMetadata).where(
        models.CADMetadata.project_id == project_id
    )
    if entity_type is not None:
        stmt = stmt.where(models.CADMetadata.entity_type == entity_type)
    if sheet_id is not None:
        stmt = stmt.where(models.CADMetadata.sheet_id == sheet_id)
    stmt = stmt.order_by(models.CADMetadata.entity_type, models.CADMetadata.entity_label)
    return list(db.scalars(stmt).all())


def list_cad_metadata_for_sheet(
    db: Session, sheet_id: str
) -> list[models.CADMetadata]:
    stmt = (
        select(models.CADMetadata)
        .where(models.CADMetadata.sheet_id == sheet_id)
        .order_by(models.CADMetadata.entity_type, models.CADMetadata.entity_label)
    )
    return list(db.scalars(stmt).all())


def entity_type_counts(db: Session, project_id: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in list_cad_metadata(db, project_id):
        counts[record.entity_type] = counts.get(record.entity_type, 0) + 1
    return counts
