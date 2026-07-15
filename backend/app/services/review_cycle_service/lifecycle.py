"""Review cycle lifecycle: create, ensure, load, and status helpers.

A reviewer can create or load a review cycle for a project, list cycles, and
read a cycle summary. Review cycles organize multi-round review-support work.
They do not approve plans, certify compliance, or make final engineering
decisions.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.review_cycle_service._common import (
    _audit,
    _latest_response_package,
    _now,
    _require_project,
    _short,
)
from app.services.review_cycle_service.errors import ReviewCycleError


def create_review_cycle(
    db: Session,
    *,
    project_id: str,
    cycle_number: int | None = None,
    cycle_name: str | None = None,
    source_response_package_id: str | None = None,
    source_workflow_board_id: str | None = None,
    summary: str | None = None,
) -> models.ReviewCycle:
    _require_project(db, project_id)
    existing = list_review_cycles(db, project_id)
    if cycle_number is None:
        cycle_number = (max((c.cycle_number for c in existing), default=0)) + 1
    if cycle_name is None:
        cycle_name = (
            "Initial review" if cycle_number == 1 else f"Review round {cycle_number}"
        )
    if source_response_package_id is None:
        package = _latest_response_package(db, project_id)
        source_response_package_id = (
            package.response_package_id if package is not None else None
        )
    if source_workflow_board_id is None:
        source_workflow_board_id = project_id

    cycle = models.ReviewCycle(
        review_cycle_id=f"cycle_{_short()}",
        project_id=project_id,
        cycle_number=cycle_number,
        cycle_name=cycle_name,
        status="active",
        started_at=_now(),
        source_response_package_id=source_response_package_id,
        source_workflow_board_id=source_workflow_board_id,
        summary=summary
        or (
            f"Review cycle {cycle_number} for the project. Tracks resubmittals, "
            "applicant responses, DXF revision comparison, and carry-forward "
            "items under human review."
        ),
        requires_human_review=True,
    )
    db.add(cycle)
    _audit(
        db,
        project_id=project_id,
        event_type="review_cycle_created",
        related_entity_type="review_cycle",
        related_entity_id=cycle.review_cycle_id,
        description=f"Review cycle {cycle_number} created.",
        metadata={"review_cycle_id": cycle.review_cycle_id, "cycle_number": cycle_number},
    )
    db.commit()
    db.refresh(cycle)
    return cycle


def ensure_review_cycle(db: Session, project_id: str) -> None:
    """Create the initial review cycle once if none exists for the project."""

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.ReviewCycle)
        .filter(models.ReviewCycle.project_id == project_id)
        .first()
    )
    if existing is None:
        create_review_cycle(db, project_id=project_id, cycle_number=1)


def list_review_cycles(db: Session, project_id: str) -> list[models.ReviewCycle]:
    return list(
        db.scalars(
            select(models.ReviewCycle)
            .where(models.ReviewCycle.project_id == project_id)
            .order_by(models.ReviewCycle.cycle_number)
        ).all()
    )


def get_review_cycle_record(
    db: Session, review_cycle_id: str
) -> models.ReviewCycle | None:
    return db.scalars(
        select(models.ReviewCycle).where(
            models.ReviewCycle.review_cycle_id == review_cycle_id
        )
    ).first()


def get_review_cycle(
    db: Session, review_cycle_id: str
) -> models.ReviewCycle | None:
    cycle = get_review_cycle_record(db, review_cycle_id)
    if cycle is None:
        return None
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="review_cycle_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Review cycle viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return cycle


def _active_cycle(db: Session, project_id: str) -> models.ReviewCycle | None:
    cycles = list_review_cycles(db, project_id)
    if not cycles:
        return None
    for cycle in reversed(cycles):
        if cycle.status in {"active", "draft"}:
            return cycle
    return cycles[-1]


def get_review_cycle_summary(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    cycles = list_review_cycles(db, project_id)
    statuses: dict[str, int] = {}
    for cycle in cycles:
        statuses[cycle.status] = statuses.get(cycle.status, 0) + 1
    active = _active_cycle(db, project_id)
    return {
        "project_id": project_id,
        "cycle_count": len(cycles),
        "active_cycle_id": active.review_cycle_id if active else None,
        "active_cycle_number": active.cycle_number if active else None,
        "statuses": statuses,
        "note": (
            "Review cycles organize multi-round review-support work. They do not "
            "approve plans, certify compliance, or make final engineering decisions."
        ),
    }


def _require_cycle(db: Session, review_cycle_id: str) -> models.ReviewCycle:
    cycle = get_review_cycle_record(db, review_cycle_id)
    if cycle is None:
        raise ReviewCycleError("Review cycle not found.", status_code=404)
    return cycle
