"""Plan sheet service for the Phase 6 plan sheet index.

This service reads the seeded Brookside Meadows plan sheet index and computes a
sheet index summary. It identifies missing and referenced-not-included sheets so
a reviewer can see gaps in the plan set. None of these operations is a final
design review or CAD verification; they organize plan sheet metadata for human
review.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

# Sheet statuses that indicate a gap in the submitted plan set.
GAP_STATUSES = {"missing", "referenced_not_included"}


def list_plan_sheets(db: Session, project_id: str) -> list[models.PlanSheet]:
    """Return all plan sheets for a project ordered by sheet number."""

    stmt = (
        select(models.PlanSheet)
        .where(models.PlanSheet.project_id == project_id)
        .order_by(models.PlanSheet.sheet_number)
    )
    return list(db.scalars(stmt).all())


def get_plan_sheet(db: Session, sheet_id: str) -> models.PlanSheet | None:
    """Return one plan sheet by its sheet id."""

    stmt = select(models.PlanSheet).where(models.PlanSheet.sheet_id == sheet_id)
    return db.scalars(stmt).first()


def list_missing_sheets(db: Session, project_id: str) -> list[models.PlanSheet]:
    """Return sheets that are missing or referenced but not included."""

    return [
        sheet
        for sheet in list_plan_sheets(db, project_id)
        if sheet.status in GAP_STATUSES
    ]


def plan_sheet_summary(db: Session, project_id: str) -> dict:
    """Return a summary of the plan sheet index for a project."""

    sheets = list_plan_sheets(db, project_id)
    cad_records = db.scalars(
        select(models.CadMetadata).where(
            models.CadMetadata.project_id == project_id
        )
    ).all()

    present = [s for s in sheets if s.status in {"present", "current"}]
    gaps = [s for s in sheets if s.status in GAP_STATUSES]
    needs_confirmation = [
        s for s in sheets if s.status == "needs_reviewer_confirmation"
    ]
    with_findings = [s for s in sheets if s.related_findings]

    by_discipline: dict[str, int] = {}
    for sheet in sheets:
        by_discipline[sheet.discipline] = by_discipline.get(sheet.discipline, 0) + 1

    return {
        "project_id": project_id,
        "total_sheets": len(sheets),
        "present_sheets": len(present),
        "missing_or_referenced_not_included": len(gaps),
        "needs_reviewer_confirmation": len(needs_confirmation),
        "sheets_with_related_findings": len(with_findings),
        "cad_metadata_records": len(cad_records),
        "sheets_by_discipline": by_discipline,
        "missing_sheet_ids": [s.sheet_id for s in gaps],
    }
