"""Review cycle dashboard projections.

Aggregates review-support counts across cycles, resubmittals, applicant
responses, revision comparison runs, carry-forward items, and resolution
records. The dashboard organizes review-support work. It does not approve
plans, certify compliance, or make final engineering decisions.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.review_cycle_service._common import _audit, _require_project
from app.services.review_cycle_service.carry_forward import (
    list_issue_carry_forwards,
    list_response_resolution_records,
)
from app.services.review_cycle_service.comparison import (
    list_revision_comparison_runs,
)
from app.services.review_cycle_service.errors import LIMITATIONS_NOTE
from app.services.review_cycle_service.lifecycle import (
    _active_cycle,
    list_review_cycles,
)
from app.services.review_cycle_service.responses import list_applicant_responses
from app.services.review_cycle_service.resubmittals import (
    list_resubmittal_packages,
)


def get_review_cycle_dashboard(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    cycles = list_review_cycles(db, project_id)
    active = _active_cycle(db, project_id)
    resubmittals = list_resubmittal_packages(db, project_id)
    resubmittal_statuses: dict[str, int] = {}
    for package in resubmittals:
        resubmittal_statuses[package.status] = (
            resubmittal_statuses.get(package.status, 0) + 1
        )
    responses = list_applicant_responses(db, project_id)
    mapped_ids = {
        m.applicant_response_id
        for m in db.scalars(
            select(models.ApplicantResponseMapping).where(
                models.ApplicantResponseMapping.project_id == project_id
            )
        ).all()
    }
    comparison_runs = list_revision_comparison_runs(db, project_id)
    change_count = (
        db.query(models.RevisionChangeRecord)
        .filter(models.RevisionChangeRecord.project_id == project_id)
        .count()
    )
    carry_forwards = list_issue_carry_forwards(db, project_id)
    resolutions = list_response_resolution_records(db, project_id)
    resolution_statuses: dict[str, int] = {}
    for record in resolutions:
        resolution_statuses[record.status] = (
            resolution_statuses.get(record.status, 0) + 1
        )
    open_item_count = len(
        [r for r in resolutions if r.status in {"still_open", "needs_more_information", "carried_forward"}]
    )
    next_prep = None
    if active is not None:
        next_prep = db.scalars(
            select(models.NextCyclePreparation).where(
                models.NextCyclePreparation.review_cycle_id
                == active.review_cycle_id
            )
        ).first()

    _audit(
        db,
        project_id=project_id,
        event_type="review_cycle_dashboard_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Review cycle dashboard viewed.",
        metadata={"cycle_count": len(cycles)},
    )
    db.commit()
    return {
        "project_id": project_id,
        "cycle_count": len(cycles),
        "active_cycle_id": active.review_cycle_id if active else None,
        "active_cycle_number": active.cycle_number if active else None,
        "review_cycles": cycles,
        "resubmittal_count": len(resubmittals),
        "resubmittal_statuses": resubmittal_statuses,
        "applicant_response_count": len(responses),
        "unmapped_response_count": len(
            [r for r in responses if r.applicant_response_id not in mapped_ids]
        ),
        "comparison_run_count": len(comparison_runs),
        "revision_change_count": change_count,
        "carry_forward_count": len(carry_forwards),
        "resolution_count": len(resolutions),
        "resolution_statuses": resolution_statuses,
        "open_item_count": open_item_count,
        "next_cycle_ready": bool(next_prep and next_prep.next_response_package_ready),
        "limitations_note": LIMITATIONS_NOTE,
    }
