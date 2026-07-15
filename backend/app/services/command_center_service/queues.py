"""Command center snapshot generation and the derived attention queues."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.command_center.attention import _build_attention_items
from app.services.command_center.derivations import (
    _comparisons_needing_review,
    _low_confidence_mappings,
    _open_carry_forwards,
    _open_follow_ups,
    _unmapped_responses,
)
from app.services.command_center.metrics import _build_metrics
from app.services.command_center.readiness import _build_readiness_checks
from app.services.command_center.timeline import _build_timeline_events
from app.services.command_center_service._common import (
    _audit,
    _gather,
    _now,
    _require_project,
    _short,
    get_latest_snapshot_record,
)


# ---------------------------------------------------------------------------
# Snapshot generation
# ---------------------------------------------------------------------------


def _delete_previous_snapshots(db: Session, project_id: str) -> dict:
    """Delete prior snapshots and their children, returning prior attention status.

    Returns a map of (source_type, source_id) -> status so reviewer decisions on
    attention items persist across regeneration.
    """

    prior_status: dict[tuple[str, str | None], str] = {}
    snapshots = list(
        db.scalars(
            select(models.ProjectCommandCenterSnapshot).where(
                models.ProjectCommandCenterSnapshot.project_id == project_id
            )
        ).all()
    )
    for snapshot in snapshots:
        for item in db.scalars(
            select(models.ReviewerAttentionItem).where(
                models.ReviewerAttentionItem.snapshot_id == snapshot.snapshot_id
            )
        ).all():
            prior_status[(item.source_type, item.source_id)] = item.status
            db.delete(item)
        for metric in db.scalars(
            select(models.ProjectHealthMetric).where(
                models.ProjectHealthMetric.snapshot_id == snapshot.snapshot_id
            )
        ).all():
            db.delete(metric)
        for check in db.scalars(
            select(models.ReviewReadinessCheck).where(
                models.ReviewReadinessCheck.snapshot_id == snapshot.snapshot_id
            )
        ).all():
            db.delete(check)
        db.delete(snapshot)

    # Timeline events are project-level and rebuilt each generation.
    for event in db.scalars(
        select(models.ProjectTimelineEvent).where(
            models.ProjectTimelineEvent.project_id == project_id
        )
    ).all():
        db.delete(event)

    db.flush()
    return prior_status


def generate_command_center_snapshot(
    db: Session, project_id: str
) -> models.ProjectCommandCenterSnapshot:
    """Aggregate all review-support data into a fresh command center snapshot.

    Regenerating preserves the reviewer status of attention items by matching
    source, so it never creates duplicate attention items for the same source.
    """

    _require_project(db, project_id)
    prior_status = _delete_previous_snapshots(db, project_id)

    data = _gather(db, project_id)
    # Attach response packages for the timeline (separate query, latest first).
    data["response_packages"] = list(
        db.scalars(
            select(models.ResponsePackage)
            .where(models.ResponsePackage.project_id == project_id)
            .order_by(models.ResponsePackage.created_at)
        ).all()
    )

    active_cycle = data["active_cycle"]
    snapshot = models.ProjectCommandCenterSnapshot(
        snapshot_id=f"cc_{_short()}",
        project_id=project_id,
        current_review_cycle_id=(
            active_cycle.review_cycle_id if active_cycle else None
        ),
        generated_at=_now(),
        overall_status="active_review",
        summary="",
        requires_human_review=True,
    )
    db.add(snapshot)
    db.flush()

    attention_items = _build_attention_items(
        data, snapshot.snapshot_id, project_id, prior_status
    )
    for item in attention_items:
        db.add(item)
    for metric in _build_metrics(data, snapshot.snapshot_id, project_id):
        db.add(metric)
    for check in _build_readiness_checks(data, snapshot.snapshot_id, project_id):
        db.add(check)
    for event in _build_timeline_events(data, project_id):
        db.add(event)

    open_items = [i for i in attention_items if i.status == "open"]
    handoff_count = len(
        [i for i in data["workflow_items"] if i.status == "ready_for_handoff"]
    )
    carry_forward_count = len(_open_carry_forwards(data))
    needs_more_info = (
        len(
            [
                i
                for i in data["workflow_items"]
                if i.status == "needs_more_information"
            ]
        )
        + len(
            [r for r in data["resolutions"] if r.status == "needs_more_information"]
        )
        + len(
            [
                r
                for r in data["applicant_responses"]
                if r.status == "needs_clarification"
            ]
        )
    )
    mapping_gap = len(_unmapped_responses(data)) + len(_low_confidence_mappings(data))
    revision_needing = sum(c for _run, c in _comparisons_needing_review(data))
    open_follow_up_count = len(_open_follow_ups(data))

    snapshot.attention_count = len(open_items)
    snapshot.ready_for_handoff_count = handoff_count
    snapshot.carry_forward_count = carry_forward_count
    snapshot.needs_more_information_count = needs_more_info
    snapshot.cad_findings_count = len(data["cad_findings"])
    snapshot.resubmittal_count = len(data["resubmittals"])
    snapshot.open_follow_up_count = open_follow_up_count
    snapshot.response_mapping_gap_count = mapping_gap
    snapshot.revision_change_count = revision_needing

    snapshot.overall_status = _overall_status(
        open_items, handoff_count, needs_more_info
    )
    snapshot.summary = _summary_text(
        data, snapshot, active_cycle
    )

    _audit(
        db,
        project_id=project_id,
        event_type="command_center_snapshot_generated",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center snapshot generated.",
        metadata={
            "snapshot_id": snapshot.snapshot_id,
            "attention_count": snapshot.attention_count,
            "overall_status": snapshot.overall_status,
        },
    )
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _overall_status(open_items: list, handoff_count: int, needs_more_info: int) -> str:
    if not open_items and handoff_count > 0:
        return "ready_for_handoff"
    if any(i.severity in {"high", "needs_human_review"} for i in open_items):
        return "needs_attention"
    if needs_more_info > 0:
        return "needs_more_information"
    if open_items:
        return "active_review"
    return "active_review"


def _summary_text(data: dict, snapshot, active_cycle) -> str:
    cycle_label = (
        f"review round {active_cycle.cycle_number}" if active_cycle else "no active cycle"
    )
    return (
        f"Brookside Meadows is in {cycle_label}. {snapshot.attention_count} item(s) "
        f"need attention, {snapshot.ready_for_handoff_count} ready for handoff "
        f"review, {snapshot.carry_forward_count} carried forward, "
        f"{snapshot.response_mapping_gap_count} response mapping gap(s), and "
        f"{snapshot.cad_findings_count} CAD finding(s). This is a review-support "
        "summary and is not a final decision: nothing here approves, certifies, "
        "verifies, validates, closes, or resolves the project."
    )


def _ensure_snapshot(
    db: Session, project_id: str
) -> models.ProjectCommandCenterSnapshot:
    snapshot = get_latest_snapshot_record(db, project_id)
    if snapshot is None:
        snapshot = generate_command_center_snapshot(db, project_id)
    return snapshot
