"""Plan sheet hotspot and sheet viewer service for Phase 7.

This service reads seeded plan sheet hotspots and assembles the sheet viewer
context: a plan sheet plus its hotspots and the related CAD-aware metadata, plan
references, and plan consistency findings. Hotspots are seeded review-support
annotations over a synthetic plan sheet preview, not extracted CAD geometry or
verified plan locations. Nothing here verifies a drawing or validates a design.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

# Shown in the viewer so the synthetic preview is never mistaken for a real
# drawing or extracted CAD geometry.
PREVIEW_NOTE = (
    "This sheet preview and its hotspots are seeded review-support metadata, "
    "not extracted CAD or verified plan geometry."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_plan_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type="system",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def list_sheet_hotspots(
    db: Session, project_id: str
) -> list[models.PlanSheetHotspot]:
    """Return all sheet hotspots for a project."""

    stmt = (
        select(models.PlanSheetHotspot)
        .where(models.PlanSheetHotspot.project_id == project_id)
        .order_by(models.PlanSheetHotspot.hotspot_id)
    )
    return list(db.scalars(stmt).all())


def list_hotspots_for_sheet(
    db: Session, sheet_id: str
) -> list[models.PlanSheetHotspot]:
    """Return hotspots placed on a single plan sheet."""

    stmt = (
        select(models.PlanSheetHotspot)
        .where(models.PlanSheetHotspot.sheet_id == sheet_id)
        .order_by(models.PlanSheetHotspot.hotspot_id)
    )
    return list(db.scalars(stmt).all())


def get_sheet_hotspot(
    db: Session, hotspot_id: str
) -> models.PlanSheetHotspot | None:
    """Return one sheet hotspot by id."""

    stmt = select(models.PlanSheetHotspot).where(
        models.PlanSheetHotspot.hotspot_id == hotspot_id
    )
    return db.scalars(stmt).first()


def inspect_sheet_hotspot(
    db: Session, hotspot_id: str
) -> models.PlanSheetHotspot | None:
    """Return one hotspot and record that it was inspected.

    Writes a lightweight audit event so the decision history shows which
    hotspots a reviewer opened. Returns None if the hotspot does not exist.
    """

    hotspot = get_sheet_hotspot(db, hotspot_id)
    if hotspot is None:
        return None
    _audit(
        db,
        project_id=hotspot.project_id,
        event_type="sheet_hotspot_inspected",
        related_entity_type="plan_sheet_hotspot",
        related_entity_id=hotspot.hotspot_id,
        description=(
            f"Sheet hotspot inspected: {hotspot.label} on sheet "
            f"{hotspot.sheet_id}."
        ),
        metadata={
            "hotspot_id": hotspot.hotspot_id,
            "sheet_id": hotspot.sheet_id,
            "hotspot_type": hotspot.hotspot_type,
        },
    )
    db.commit()
    return hotspot


def summarize_sheet_hotspots(db: Session, project_id: str) -> dict:
    """Return counts of seeded sheet hotspots for a project."""

    hotspots = list_sheet_hotspots(db, project_id)
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for hotspot in hotspots:
        by_type[hotspot.hotspot_type] = by_type.get(hotspot.hotspot_type, 0) + 1
        by_severity[hotspot.severity] = by_severity.get(hotspot.severity, 0) + 1

    return {
        "project_id": project_id,
        "total_hotspots": len(hotspots),
        "sheets_with_hotspots": len({h.sheet_id for h in hotspots}),
        "hotspots_by_type": by_type,
        "hotspots_by_severity": by_severity,
        "hotspots_requiring_human_review": len(
            [h for h in hotspots if h.requires_human_review]
        ),
    }


def get_plan_view_context(db: Session, sheet_id: str) -> dict | None:
    """Assemble the sheet viewer context for one plan sheet.

    Returns the sheet, its hotspots, the CAD-aware metadata on the sheet, the
    plan references that touch the sheet (directly or through a feature on it),
    and the plan consistency findings related to the sheet. Writes an audit
    event that the viewer context was requested. Returns None if the sheet does
    not exist.
    """

    sheet = db.scalars(
        select(models.PlanSheet).where(models.PlanSheet.sheet_id == sheet_id)
    ).first()
    if sheet is None:
        return None

    hotspots = list_hotspots_for_sheet(db, sheet_id)

    cad_records = list(
        db.scalars(
            select(models.CadMetadata).where(
                models.CadMetadata.sheet_id == sheet_id
            )
        ).all()
    )
    cad_ids_on_sheet = {c.cad_metadata_id for c in cad_records}

    # Plan references that touch the sheet directly or via a feature on it.
    all_refs = list(
        db.scalars(
            select(models.PlanReference).where(
                models.PlanReference.project_id == sheet.project_id
            )
        ).all()
    )
    touch_ids = {sheet_id} | cad_ids_on_sheet
    references = [
        r
        for r in all_refs
        if r.source_id in touch_ids or r.target_id in touch_ids
    ]

    # Plan consistency findings related to the sheet directly or via a feature.
    all_findings = list(
        db.scalars(
            select(models.PlanConsistencyFinding).where(
                models.PlanConsistencyFinding.project_id == sheet.project_id
            )
        ).all()
    )
    findings = [
        f
        for f in all_findings
        if sheet_id in (f.related_sheet_ids or [])
        or (set(f.related_cad_metadata_ids or []) & cad_ids_on_sheet)
    ]

    _audit(
        db,
        project_id=sheet.project_id,
        event_type="sheet_viewer_context_requested",
        related_entity_type="plan_sheet",
        related_entity_id=sheet_id,
        description=(
            f"Sheet viewer context requested for {sheet.sheet_number} "
            f"({sheet.sheet_title})."
        ),
        metadata={
            "sheet_id": sheet_id,
            "hotspot_count": len(hotspots),
            "reference_count": len(references),
            "finding_count": len(findings),
        },
    )
    db.commit()

    return {
        "sheet": sheet,
        "hotspots": hotspots,
        "cad_metadata": cad_records,
        "plan_references": references,
        "plan_consistency_findings": findings,
        "preview_note": PREVIEW_NOTE,
    }
