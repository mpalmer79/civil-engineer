"""DXF revision comparison between two parse runs.

Compares extracted DXF metadata between two parse runs: layers and review
categories, reference candidates (sheet, detail, pipe, basin, outfall, and
wetland buffer references and other text), block names, and CAD review findings.
It does not compare geometry in a way that implies engineering validation and
never verifies CAD or validates design. All statuses are review-support
statuses, not final engineering decisions.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import cad_intake_service
from app.services.review_cycle_service._common import (
    _audit,
    _now,
    _require_project,
    _short,
    _stem,
)
from app.services.review_cycle_service.errors import (
    FINDING_TYPE_TO_CATEGORY,
    LIMITATIONS_NOTE,
    REF_TYPE_TO_CATEGORY,
    STEM_CATEGORIES,
    ReviewCycleError,
)
from app.services.review_cycle_service.lifecycle import _require_cycle
from app.services.review_cycle_service.resubmittals import (
    get_resubmittal_package_record,
)


def _findings_for_run(db: Session, parse_run_id: str) -> list:
    return list(
        db.scalars(
            select(models.CadReviewFinding).where(
                models.CadReviewFinding.parse_run_id == parse_run_id
            )
        ).all()
    )


def _round_metadata(db: Session, parse_run_id: str) -> dict:
    layers = {
        layer.layer_name: layer.review_category
        for layer in cad_intake_service.list_cad_layers(
            db, parse_run_id, audit=False
        )
    }
    blocks = {
        block.block_name: block.block_name
        for block in cad_intake_service.list_cad_blocks(db, parse_run_id)
    }
    references: dict[str, dict[str, str]] = {}
    for candidate in cad_intake_service.list_cad_reference_candidates(
        db, parse_run_id
    ):
        category = REF_TYPE_TO_CATEGORY.get(
            candidate.reference_type, "text_reference"
        )
        key = (
            _stem(candidate.normalized_reference)
            if category in STEM_CATEGORIES
            else candidate.normalized_reference
        )
        references.setdefault(category, {})[key] = candidate.reference_text
    findings = {}
    for finding in _findings_for_run(db, parse_run_id):
        # Key by the full title (not stemmed) so distinct findings such as a
        # missing C-9.9 sheet and a missing C-8.8 sheet stay separate.
        key = (finding.finding_type, finding.title.strip().upper())
        findings[key] = finding
    return {"layers": layers, "blocks": blocks, "references": references, "findings": findings}


def _change_severity(change_type: str) -> str:
    return {
        "added": "low",
        "removed": "medium",
        "changed": "medium",
        "carried_forward": "medium",
        "unchanged": "low",
    }.get(change_type, "low")


def run_revision_comparison(
    db: Session,
    *,
    project_id: str,
    review_cycle_id: str,
    previous_parse_run_id: str,
    current_parse_run_id: str,
    resubmittal_package_id: str | None = None,
) -> models.RevisionComparisonRun:
    """Compare extracted DXF metadata between two parse runs.

    Compares layers and review categories, reference candidates (sheet, detail,
    pipe, basin, outfall, and wetland buffer references and other text), block
    names, and CAD review findings. It does not compare geometry in a way that
    implies engineering validation and never verifies CAD or validates design.
    """

    _require_project(db, project_id)
    cycle = _require_cycle(db, review_cycle_id)
    previous = cad_intake_service.get_cad_parse_run(db, previous_parse_run_id)
    current = cad_intake_service.get_cad_parse_run(db, current_parse_run_id)
    if previous is None or current is None:
        raise ReviewCycleError("Parse run not found.", status_code=404)

    run = models.RevisionComparisonRun(
        comparison_run_id=f"rev_{_short()}",
        project_id=project_id,
        review_cycle_id=review_cycle_id,
        resubmittal_package_id=resubmittal_package_id,
        previous_parse_run_id=previous_parse_run_id,
        current_parse_run_id=current_parse_run_id,
        status="draft",
        summary="",
        limitations_note=LIMITATIONS_NOTE,
        requires_human_review=True,
    )
    db.add(run)
    db.flush()

    prev_meta = _round_metadata(db, previous_parse_run_id)
    cur_meta = _round_metadata(db, current_parse_run_id)

    counts = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0, "carried_forward": 0}

    def add_record(
        change_type: str,
        source_category: str,
        normalized_key: str,
        *,
        previous_value: str | None = None,
        current_value: str | None = None,
        layer_name: str | None = None,
        reference_type: str | None = None,
        severity: str | None = None,
        reviewer_status: str = "draft",
        linked_cad_review_finding_id: str | None = None,
    ) -> None:
        counts[change_type] = counts.get(change_type, 0) + 1
        db.add(
            models.RevisionChangeRecord(
                change_record_id=f"chg_{_short()}",
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                comparison_run_id=run.comparison_run_id,
                change_type=change_type,
                source_category=source_category,
                previous_value=previous_value,
                current_value=current_value,
                normalized_key=normalized_key,
                layer_name=layer_name,
                reference_type=reference_type,
                severity=severity or _change_severity(change_type),
                linked_cad_review_finding_id=linked_cad_review_finding_id,
                reviewer_status=reviewer_status,
                requires_human_review=change_type != "unchanged",
            )
        )

    # Layers (key = layer name, value = review category).
    prev_layers = prev_meta["layers"]
    cur_layers = cur_meta["layers"]
    for name in sorted(set(prev_layers) | set(cur_layers)):
        if name not in prev_layers:
            add_record("added", "layer", name, current_value=cur_layers[name], layer_name=name)
        elif name not in cur_layers:
            add_record("removed", "layer", name, previous_value=prev_layers[name], layer_name=name)
        elif prev_layers[name] != cur_layers[name]:
            add_record(
                "changed",
                "layer",
                name,
                previous_value=prev_layers[name],
                current_value=cur_layers[name],
                layer_name=name,
            )
        else:
            add_record("unchanged", "layer", name, previous_value=prev_layers[name], current_value=cur_layers[name], layer_name=name)

    # Blocks (key = block name).
    prev_blocks = prev_meta["blocks"]
    cur_blocks = cur_meta["blocks"]
    for name in sorted(set(prev_blocks) | set(cur_blocks)):
        if name not in prev_blocks:
            add_record("added", "block", name, current_value=name)
        elif name not in cur_blocks:
            add_record("removed", "block", name, previous_value=name)
        else:
            add_record("unchanged", "block", name, previous_value=name, current_value=name)

    # Reference candidates by category.
    prev_refs = prev_meta["references"]
    cur_refs = cur_meta["references"]
    for category in sorted(set(prev_refs) | set(cur_refs)):
        prev_map = prev_refs.get(category, {})
        cur_map = cur_refs.get(category, {})
        for key in sorted(set(prev_map) | set(cur_map)):
            if key not in prev_map:
                add_record(
                    "added",
                    category,
                    key,
                    current_value=cur_map[key],
                    reference_type=category,
                )
            elif key not in cur_map:
                add_record(
                    "removed",
                    category,
                    key,
                    previous_value=prev_map[key],
                    reference_type=category,
                )
            elif prev_map[key] != cur_map[key]:
                add_record(
                    "changed",
                    category,
                    key,
                    previous_value=prev_map[key],
                    current_value=cur_map[key],
                    reference_type=category,
                )
            else:
                add_record(
                    "unchanged",
                    category,
                    key,
                    previous_value=prev_map[key],
                    current_value=cur_map[key],
                    reference_type=category,
                )

    # CAD review findings (key = finding type + normalized title).
    prev_findings = prev_meta["findings"]
    cur_findings = cur_meta["findings"]
    for key in sorted(set(prev_findings) | set(cur_findings), key=lambda k: (k[0], k[1])):
        finding_type, _title = key
        category = FINDING_TYPE_TO_CATEGORY.get(finding_type, "unknown")
        if key not in prev_findings:
            finding = cur_findings[key]
            add_record(
                "added",
                category,
                finding.title,
                current_value=finding.title,
                severity=finding.severity,
                linked_cad_review_finding_id=finding.cad_review_finding_id,
            )
        elif key not in cur_findings:
            finding = prev_findings[key]
            add_record(
                "removed",
                category,
                finding.title,
                previous_value=finding.title,
                severity="low",
            )
        else:
            finding = cur_findings[key]
            add_record(
                "carried_forward",
                category,
                finding.title,
                previous_value=prev_findings[key].title,
                current_value=finding.title,
                severity=finding.severity,
                reviewer_status="carried_forward",
                linked_cad_review_finding_id=finding.cad_review_finding_id,
            )

    warning_count = counts["carried_forward"]
    run.compared_layer_count = len(set(prev_layers) | set(cur_layers))
    run.compared_text_count = sum(
        len(set(prev_refs.get(c, {})) | set(cur_refs.get(c, {})))
        for c in set(prev_refs) | set(cur_refs)
    )
    run.added_count = counts["added"]
    run.removed_count = counts["removed"]
    run.changed_count = counts["changed"]
    run.unchanged_count = counts["unchanged"]
    run.warning_count = warning_count
    run.completed_at = _now()
    run.status = "completed_with_warnings" if warning_count else "completed"
    run.summary = (
        f"Compared DXF metadata: {counts['added']} added, {counts['removed']} "
        f"removed, {counts['changed']} changed, {counts['carried_forward']} "
        f"carried forward, {counts['unchanged']} unchanged references. Review-support only."
    )

    # Mark the resubmittal as comparison complete if linked.
    if resubmittal_package_id:
        package = get_resubmittal_package_record(db, resubmittal_package_id)
        if package is not None and package.status in {
            "received",
            "intake_review",
            "ready_for_comparison",
        }:
            package.status = "comparison_complete"
            package.updated_at = _now()

    _audit(
        db,
        project_id=project_id,
        event_type="revision_comparison_run",
        related_entity_type="revision_comparison_run",
        related_entity_id=run.comparison_run_id,
        description="DXF revision comparison run.",
        metadata={
            "comparison_run_id": run.comparison_run_id,
            "review_cycle_id": review_cycle_id,
            "added": counts["added"],
            "removed": counts["removed"],
            "changed": counts["changed"],
            "carried_forward": counts["carried_forward"],
        },
    )
    db.commit()
    db.refresh(run)
    return run


def get_revision_comparison_run_record(
    db: Session, comparison_run_id: str
) -> models.RevisionComparisonRun | None:
    return db.scalars(
        select(models.RevisionComparisonRun).where(
            models.RevisionComparisonRun.comparison_run_id == comparison_run_id
        )
    ).first()


def get_revision_comparison_run(
    db: Session, comparison_run_id: str
) -> models.RevisionComparisonRun | None:
    run = get_revision_comparison_run_record(db, comparison_run_id)
    if run is None:
        return None
    _audit(
        db,
        project_id=run.project_id,
        event_type="revision_comparison_viewed",
        related_entity_type="revision_comparison_run",
        related_entity_id=comparison_run_id,
        description="Revision comparison run viewed.",
        metadata={"comparison_run_id": comparison_run_id},
    )
    db.commit()
    return run


def list_revision_comparison_runs(
    db: Session, project_id: str
) -> list[models.RevisionComparisonRun]:
    return list(
        db.scalars(
            select(models.RevisionComparisonRun)
            .where(models.RevisionComparisonRun.project_id == project_id)
            .order_by(models.RevisionComparisonRun.started_at.desc())
        ).all()
    )


def list_revision_change_records(
    db: Session, comparison_run_id: str, *, audit: bool = True
) -> list[models.RevisionChangeRecord]:
    records = list(
        db.scalars(
            select(models.RevisionChangeRecord)
            .where(
                models.RevisionChangeRecord.comparison_run_id == comparison_run_id
            )
            .order_by(models.RevisionChangeRecord.id)
        ).all()
    )
    if audit and records:
        run = get_revision_comparison_run_record(db, comparison_run_id)
        if run is not None:
            _audit(
                db,
                project_id=run.project_id,
                event_type="revision_changes_viewed",
                related_entity_type="revision_comparison_run",
                related_entity_id=comparison_run_id,
                description="Revision change records viewed.",
                metadata={"comparison_run_id": comparison_run_id, "count": len(records)},
            )
            db.commit()
    return records


def summarize_revision_changes(db: Session, comparison_run_id: str) -> dict | None:
    run = get_revision_comparison_run_record(db, comparison_run_id)
    if run is None:
        return None
    records = list_revision_change_records(db, comparison_run_id, audit=False)
    by_category: dict[str, int] = {}
    by_type: dict[str, int] = {}
    carried = 0
    for record in records:
        by_category[record.source_category] = (
            by_category.get(record.source_category, 0) + 1
        )
        by_type[record.change_type] = by_type.get(record.change_type, 0) + 1
        if record.change_type == "carried_forward":
            carried += 1
    return {
        "comparison_run_id": comparison_run_id,
        "project_id": run.project_id,
        "review_cycle_id": run.review_cycle_id,
        "status": run.status,
        "added_count": run.added_count,
        "removed_count": run.removed_count,
        "changed_count": run.changed_count,
        "unchanged_count": run.unchanged_count,
        "carried_forward_count": carried,
        "changes_by_category": by_category,
        "changes_by_type": by_type,
        "limitations_note": run.limitations_note,
        "note": (
            "Counts describe extracted DXF metadata differences for review "
            "support. They do not verify CAD or validate the design."
        ),
    }
