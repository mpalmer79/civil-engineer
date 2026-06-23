"""CAD-aware metadata service for the Phase 6 foundation.

This service reads seeded CAD-aware feature metadata for the Brookside Meadows
fixture. The metadata is seeded, not extracted from DWG or DXF files, and it
does not verify any drawing as correct. It provides a future-ready abstraction
for CAD-derived metadata: callers can list feature-level metadata for a project,
filter by entity type, or list metadata for a single plan sheet.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def list_cad_metadata(
    db: Session, project_id: str, entity_type: str | None = None
) -> list[models.CadMetadata]:
    """Return CAD metadata for a project, optionally filtered by entity type."""

    stmt = select(models.CadMetadata).where(
        models.CadMetadata.project_id == project_id
    )
    if entity_type is not None:
        stmt = stmt.where(models.CadMetadata.entity_type == entity_type)
    stmt = stmt.order_by(models.CadMetadata.entity_label)
    return list(db.scalars(stmt).all())


def list_cad_metadata_for_sheet(
    db: Session, sheet_id: str
) -> list[models.CadMetadata]:
    """Return CAD metadata records linked to a single plan sheet."""

    stmt = (
        select(models.CadMetadata)
        .where(models.CadMetadata.sheet_id == sheet_id)
        .order_by(models.CadMetadata.entity_label)
    )
    return list(db.scalars(stmt).all())


def get_cad_metadata(
    db: Session, cad_metadata_id: str
) -> models.CadMetadata | None:
    """Return one CAD metadata record by id."""

    stmt = select(models.CadMetadata).where(
        models.CadMetadata.cad_metadata_id == cad_metadata_id
    )
    return db.scalars(stmt).first()


def entity_type_counts(db: Session, project_id: str) -> dict[str, int]:
    """Return a count of CAD metadata records by entity type."""

    counts: dict[str, int] = {}
    for record in list_cad_metadata(db, project_id):
        counts[record.entity_type] = counts.get(record.entity_type, 0) + 1
    return counts
