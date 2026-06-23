"""Plan sheet read service.

Provides read access to the seeded Brookside Meadows plan sheet index and a
sheet index summary. Plan sheets are review-support metadata, not parsed CAD
files and not approved drawings.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

# Sheet statuses that mean the sheet is part of the submitted package.
_PRESENT_STATUSES = {"present", "current", "superseded", "needs_reviewer_confirmation"}
# Sheet statuses that mean the sheet is expected but not usable as submitted.
_MISSING_STATUSES = {"missing", "referenced_not_included"}


def list_plan_sheets(db: Session, project_id: str) -> list[models.PlanSheet]:
    stmt = (
        select(models.PlanSheet)
        .where(models.PlanSheet.project_id == project_id)
        .order_by(models.PlanSheet.sheet_number)
    )
    return list(db.scalars(stmt).all())


def get_plan_sheet(db: Session, sheet_id: str) -> models.PlanSheet | None:
    return db.scalars(
        select(models.PlanSheet).where(models.PlanSheet.sheet_id == sheet_id)
    ).first()


def plan_sheet_summary(db: Session, project_id: str) -> dict:
    """Return a sheet index summary with review-support counts."""

    sheets = list_plan_sheets(db, project_id)
    present = [s for s in sheets if s.status in _PRESENT_STATUSES]
    missing = [s for s in sheets if s.status in _MISSING_STATUSES]
    with_findings = [s for s in sheets if s.related_findings]

    cad_count = (
        db.query(models.CADMetadata)
        .filter(models.CADMetadata.project_id == project_id)
        .count()
    )

    disciplines: dict[str, int] = {}
    for s in sheets:
        disciplines[s.discipline] = disciplines.get(s.discipline, 0) + 1

    return {
        "project_id": project_id,
        "total_sheets": len(sheets),
        "present_sheets": len(present),
        "missing_or_referenced_not_included_sheets": len(missing),
        "sheets_with_related_findings": len(with_findings),
        "cad_metadata_records": cad_count,
        "disciplines": disciplines,
        "missing_sheet_numbers": [s.sheet_number for s in missing],
    }
