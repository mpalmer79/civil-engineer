"""Issue carry-forward, response resolution, and next-cycle preparation.

Carries unresolved review-support items forward without duplication, records
review-support resolution statuses, and prepares the next review cycle.
Resolution statuses such as addressed_for_review are review-support states,
never final decisions like resolved, closed, approved, or certified. Nothing
here is a final engineering decision.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import ALLOWED_RESOLUTION_STATUSES
from app.db import models
from app.services import cad_intake_service, workflow_service
from app.services.review_cycle_service._common import (
    _audit,
    _now,
    _response_package_items,
    _short,
)
from app.services.review_cycle_service.errors import ReviewCycleError
from app.services.review_cycle_service.lifecycle import _require_cycle
from app.services.review_cycle_service.responses import list_applicant_responses


def _existing_carry_forward_sources(
    db: Session, review_cycle_id: str
) -> set[tuple[str, str]]:
    sources: set[tuple[str, str]] = set()
    for cf in db.scalars(
        select(models.IssueCarryForward).where(
            models.IssueCarryForward.review_cycle_id == review_cycle_id
        )
    ).all():
        if cf.source_workflow_item_id:
            sources.add(("workflow_item", cf.source_workflow_item_id))
        if cf.source_response_item_id:
            sources.add(("response_item", cf.source_response_item_id))
        if cf.source_cad_finding_id:
            sources.add(("cad_finding", cf.source_cad_finding_id))
        if cf.source_revision_change_id:
            sources.add(("revision_change", cf.source_revision_change_id))
    return sources


def _add_carry_forward(
    db: Session,
    *,
    project_id: str,
    review_cycle_id: str,
    title: str,
    reason: str,
    carried_forward_status: str = "carried_forward",
    source_workflow_item_id: str | None = None,
    source_response_item_id: str | None = None,
    source_cad_finding_id: str | None = None,
    source_revision_change_id: str | None = None,
    reviewer_name: str = "reviewer",
    reviewer_note: str | None = None,
) -> models.IssueCarryForward:
    carry = models.IssueCarryForward(
        carry_forward_id=f"cf_{_short()}",
        project_id=project_id,
        review_cycle_id=review_cycle_id,
        source_workflow_item_id=source_workflow_item_id,
        source_response_item_id=source_response_item_id,
        source_cad_finding_id=source_cad_finding_id,
        source_revision_change_id=source_revision_change_id,
        title=title,
        reason=reason,
        carried_forward_status=carried_forward_status,
        reviewer_name=reviewer_name,
        reviewer_note=reviewer_note,
        requires_human_review=True,
    )
    db.add(carry)
    return carry


def carry_forward_unresolved_items(
    db: Session, review_cycle_id: str, *, reviewer_name: str = "reviewer"
) -> dict:
    """Carry unresolved review-support items forward without duplication."""

    cycle = _require_cycle(db, review_cycle_id)
    project_id = cycle.project_id
    existing = _existing_carry_forward_sources(db, review_cycle_id)
    created: list[models.IssueCarryForward] = []
    skipped = 0

    # Workflow items still needing attention.
    for item in workflow_service.list_workflow_items(db, project_id):
        if item.status not in {"needs_follow_up", "needs_more_information"}:
            continue
        if ("workflow_item", item.workflow_item_id) in existing:
            skipped += 1
            continue
        created.append(
            _add_carry_forward(
                db,
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                title=item.title,
                reason=f"Workflow item still in '{item.status}'.",
                carried_forward_status=(
                    "needs_more_information"
                    if item.status == "needs_more_information"
                    else "needs_follow_up"
                ),
                source_workflow_item_id=item.workflow_item_id,
                reviewer_name=reviewer_name,
            )
        )

    # Response package items still in needs_revision or draft.
    for item in _response_package_items(db, project_id):
        if item.status not in {"needs_revision", "draft"}:
            continue
        if ("response_item", item.item_id) in existing:
            skipped += 1
            continue
        created.append(
            _add_carry_forward(
                db,
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                title=item.title,
                reason=f"Response package item still in '{item.status}'.",
                source_response_item_id=item.item_id,
                reviewer_name=reviewer_name,
            )
        )

    # CAD review findings not promoted or still needing review.
    for finding in cad_intake_service.list_cad_review_findings(db, project_id):
        if finding.promoted_to_workflow or not finding.requires_human_review:
            continue
        if finding.status == "excluded_from_packet":
            continue
        if ("cad_finding", finding.cad_review_finding_id) in existing:
            skipped += 1
            continue
        created.append(
            _add_carry_forward(
                db,
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                title=finding.title,
                reason="CAD review finding not yet promoted and needs review.",
                source_cad_finding_id=finding.cad_review_finding_id,
                reviewer_name=reviewer_name,
            )
        )

    # Revision change records marked needs_follow_up or carried_forward.
    change_records = db.scalars(
        select(models.RevisionChangeRecord).where(
            models.RevisionChangeRecord.review_cycle_id == review_cycle_id,
            models.RevisionChangeRecord.reviewer_status.in_(
                ["needs_follow_up", "carried_forward"]
            ),
        )
    ).all()
    for record in change_records:
        if ("revision_change", record.change_record_id) in existing:
            skipped += 1
            continue
        created.append(
            _add_carry_forward(
                db,
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                title=f"Revision change: {record.normalized_key}",
                reason=(
                    f"Revision change record ({record.change_type}, "
                    f"{record.source_category}) still needs review."
                ),
                carried_forward_status="needs_follow_up",
                source_revision_change_id=record.change_record_id,
                reviewer_name=reviewer_name,
            )
        )

    _audit(
        db,
        project_id=project_id,
        event_type="issue_carried_forward",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description=f"{len(created)} item(s) carried forward.",
        metadata={
            "review_cycle_id": review_cycle_id,
            "created": len(created),
            "skipped": skipped,
        },
    )
    db.commit()
    for carry in created:
        db.refresh(carry)
    return {
        "review_cycle_id": review_cycle_id,
        "project_id": project_id,
        "created_count": len(created),
        "skipped_count": skipped,
        "carry_forward_ids": [c.carry_forward_id for c in created],
        "note": (
            "Unresolved review-support items carried forward for the next round. "
            "Nothing here is a final decision."
        ),
    }


def create_issue_carry_forward(
    db: Session,
    review_cycle_id: str,
    *,
    source_workflow_item_id: str | None = None,
    source_response_item_id: str | None = None,
    source_cad_finding_id: str | None = None,
    source_revision_change_id: str | None = None,
    title: str | None = None,
    reason: str,
    reviewer_name: str = "reviewer",
    reviewer_note: str | None = None,
) -> models.IssueCarryForward:
    cycle = _require_cycle(db, review_cycle_id)
    carry = _add_carry_forward(
        db,
        project_id=cycle.project_id,
        review_cycle_id=review_cycle_id,
        title=title or "Carried-forward review-support item",
        reason=reason,
        source_workflow_item_id=source_workflow_item_id,
        source_response_item_id=source_response_item_id,
        source_cad_finding_id=source_cad_finding_id,
        source_revision_change_id=source_revision_change_id,
        reviewer_name=reviewer_name,
        reviewer_note=reviewer_note,
    )
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="issue_carried_forward",
        related_entity_type="issue_carry_forward",
        related_entity_id=carry.carry_forward_id,
        description="Issue carried forward by reviewer.",
        metadata={"carry_forward_id": carry.carry_forward_id},
    )
    db.commit()
    db.refresh(carry)
    return carry


def list_issue_carry_forwards(
    db: Session, project_id: str
) -> list[models.IssueCarryForward]:
    return list(
        db.scalars(
            select(models.IssueCarryForward)
            .where(models.IssueCarryForward.project_id == project_id)
            .order_by(models.IssueCarryForward.created_at)
        ).all()
    )


def get_carry_forward_summary(db: Session, review_cycle_id: str) -> dict:
    cycle = _require_cycle(db, review_cycle_id)
    items = [
        c
        for c in list_issue_carry_forwards(db, cycle.project_id)
        if c.review_cycle_id == review_cycle_id
    ]
    statuses: dict[str, int] = {}
    for item in items:
        statuses[item.carried_forward_status] = (
            statuses.get(item.carried_forward_status, 0) + 1
        )
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="carry_forward_summary_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Carry-forward summary viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return {
        "review_cycle_id": review_cycle_id,
        "project_id": cycle.project_id,
        "total": len(items),
        "statuses": statuses,
        "note": "Carried-forward items remain under human review.",
    }


def create_response_resolution_record(
    db: Session,
    review_cycle_id: str,
    *,
    response_package_item_id: str | None = None,
    workflow_item_id: str | None = None,
    applicant_response_id: str | None = None,
    revision_change_record_id: str | None = None,
    status: str = "still_open",
    reviewer_note: str | None = None,
    reviewer_name: str = "reviewer",
) -> models.ResponseResolutionRecord:
    cycle = _require_cycle(db, review_cycle_id)
    if status not in ALLOWED_RESOLUTION_STATUSES:
        raise ReviewCycleError(
            f"Invalid resolution status '{status}'.", status_code=422
        )
    record = models.ResponseResolutionRecord(
        resolution_record_id=f"res_{_short()}",
        project_id=cycle.project_id,
        review_cycle_id=review_cycle_id,
        response_package_item_id=response_package_item_id,
        workflow_item_id=workflow_item_id,
        applicant_response_id=applicant_response_id,
        revision_change_record_id=revision_change_record_id,
        status=status,
        reviewer_note=reviewer_note,
        reviewer_name=reviewer_name,
        requires_human_review=True,
    )
    db.add(record)
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="response_resolution_created",
        related_entity_type="response_resolution_record",
        related_entity_id=record.resolution_record_id,
        description=f"Response resolution record created with status {status}.",
        metadata={
            "resolution_record_id": record.resolution_record_id,
            "status": status,
        },
    )
    db.commit()
    db.refresh(record)
    return record


def update_response_resolution_status(
    db: Session,
    resolution_record_id: str,
    *,
    status: str,
    reviewer_note: str | None = None,
    reviewer_name: str = "reviewer",
) -> models.ResponseResolutionRecord:
    record = db.scalars(
        select(models.ResponseResolutionRecord).where(
            models.ResponseResolutionRecord.resolution_record_id
            == resolution_record_id
        )
    ).first()
    if record is None:
        raise ReviewCycleError("Resolution record not found.", status_code=404)
    if status not in ALLOWED_RESOLUTION_STATUSES:
        raise ReviewCycleError(
            f"Invalid resolution status '{status}'.", status_code=422
        )
    previous = record.status
    record.status = status
    if reviewer_note is not None:
        record.reviewer_note = reviewer_note
    record.reviewer_name = reviewer_name
    record.updated_at = _now()
    _audit(
        db,
        project_id=record.project_id,
        event_type="response_resolution_status_changed",
        related_entity_type="response_resolution_record",
        related_entity_id=resolution_record_id,
        description=f"Resolution status changed from {previous} to {status}.",
        metadata={"previous_status": previous, "new_status": status},
    )
    db.commit()
    db.refresh(record)
    return record


def list_response_resolution_records(
    db: Session, project_id: str
) -> list[models.ResponseResolutionRecord]:
    return list(
        db.scalars(
            select(models.ResponseResolutionRecord)
            .where(models.ResponseResolutionRecord.project_id == project_id)
            .order_by(models.ResponseResolutionRecord.created_at)
        ).all()
    )


def get_resolution_summary(db: Session, review_cycle_id: str) -> dict:
    cycle = _require_cycle(db, review_cycle_id)
    records = [
        r
        for r in list_response_resolution_records(db, cycle.project_id)
        if r.review_cycle_id == review_cycle_id
    ]
    statuses: dict[str, int] = {}
    for record in records:
        statuses[record.status] = statuses.get(record.status, 0) + 1
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="resolution_summary_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Resolution summary viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return {
        "review_cycle_id": review_cycle_id,
        "project_id": cycle.project_id,
        "total": len(records),
        "statuses": statuses,
        "note": (
            "Resolution statuses are review-support states. addressed_for_review "
            "means an item appears addressed for human review, never resolved, "
            "approved, or certified."
        ),
    }


def prepare_next_cycle(
    db: Session, review_cycle_id: str
) -> models.NextCyclePreparation:
    cycle = _require_cycle(db, review_cycle_id)
    project_id = cycle.project_id

    carry_forwards = [
        c
        for c in list_issue_carry_forwards(db, project_id)
        if c.review_cycle_id == review_cycle_id
    ]
    resolutions = [
        r
        for r in list_response_resolution_records(db, project_id)
        if r.review_cycle_id == review_cycle_id
    ]
    responses_needing_clarification = [
        r
        for r in list_applicant_responses(db, project_id)
        if r.review_cycle_id == review_cycle_id and r.status == "needs_clarification"
    ]
    changes_needing_review = db.scalars(
        select(models.RevisionChangeRecord).where(
            models.RevisionChangeRecord.review_cycle_id == review_cycle_id,
            models.RevisionChangeRecord.reviewer_status.in_(
                ["needs_follow_up", "needs_more_information", "carried_forward"]
            ),
        )
    ).all()

    needs_more_information_count = len(
        [r for r in resolutions if r.status == "needs_more_information"]
    ) + len(responses_needing_clarification)
    reviewer_checked_count = len(
        [r for r in resolutions if r.status == "reviewer_checked"]
    )
    open_resolution_count = len(
        [r for r in resolutions if r.status in {"still_open", "carried_forward"}]
    )
    carried_forward_count = len(carry_forwards)

    next_ready = (
        carried_forward_count + needs_more_information_count + open_resolution_count
        > 0
    )

    summary = (
        f"Next-cycle preparation: {carried_forward_count} carried-forward item(s), "
        f"{needs_more_information_count} needing more information, "
        f"{len(changes_needing_review)} revision change(s) needing review, "
        f"{reviewer_checked_count} reviewer checked. This summary organizes "
        "review-support work for the next round and is not a final decision."
    )

    existing = db.scalars(
        select(models.NextCyclePreparation).where(
            models.NextCyclePreparation.review_cycle_id == review_cycle_id
        )
    ).first()
    if existing is None:
        prep = models.NextCyclePreparation(
            next_cycle_preparation_id=f"next_{_short()}",
            project_id=project_id,
            review_cycle_id=review_cycle_id,
            status="ready_for_next_cycle" if next_ready else "draft",
            summary=summary,
            carried_forward_count=carried_forward_count,
            needs_more_information_count=needs_more_information_count,
            reviewer_checked_count=reviewer_checked_count,
            next_response_package_ready=next_ready,
            requires_human_review=True,
        )
        db.add(prep)
    else:
        prep = existing
        prep.status = "ready_for_next_cycle" if next_ready else "draft"
        prep.summary = summary
        prep.carried_forward_count = carried_forward_count
        prep.needs_more_information_count = needs_more_information_count
        prep.reviewer_checked_count = reviewer_checked_count
        prep.next_response_package_ready = next_ready
        prep.updated_at = _now()

    if next_ready and cycle.status == "active":
        cycle.status = "ready_for_next_cycle"
        cycle.updated_at = _now()

    _audit(
        db,
        project_id=project_id,
        event_type="next_cycle_prepared",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Next cycle preparation generated.",
        metadata={
            "review_cycle_id": review_cycle_id,
            "carried_forward_count": carried_forward_count,
            "needs_more_information_count": needs_more_information_count,
        },
    )
    db.commit()
    db.refresh(prep)
    return prep


def get_next_cycle_preparation(
    db: Session, review_cycle_id: str
) -> models.NextCyclePreparation | None:
    cycle = _require_cycle(db, review_cycle_id)
    prep = db.scalars(
        select(models.NextCyclePreparation).where(
            models.NextCyclePreparation.review_cycle_id == review_cycle_id
        )
    ).first()
    if prep is None:
        return None
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="next_cycle_preparation_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Next cycle preparation viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return prep
