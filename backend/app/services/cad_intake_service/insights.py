"""Summaries, comparison, parse queue, dashboard, and review context.

Aggregated read-support views over parsed CAD data: per-run summaries, a
comparison of extracted references to seeded plan sheets, the per-project parse
queue, the intake dashboard, and the review context for a single CAD file. Each
view writes an audit event so the decision history shows reviewer access. None of
these views verify CAD, validate design, or make a final engineering decision.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import ALLOWED_CAD_QUEUE_STATUSES
from app.db import models
from app.services import plan_sheet_service
from app.services.cad_intake_service._common import (
    _audit,
    _create_finding,
    _seeded_sheet_map,
)
from app.services.cad_intake_service.errors import (
    CONTEXT_NOTE,
    CadIntakeError,
    LIMITATIONS_NOTE,
)
from app.services.cad_intake_service.reads import (
    get_cad_file,
    get_cad_parse_run,
    list_cad_files,
    list_cad_layers,
    list_cad_parse_runs,
    list_cad_reference_candidates,
    list_cad_review_findings,
)


def get_cad_parse_summary(
    db: Session, parse_run_id: str, *, audit: bool = True
) -> dict | None:
    run = get_cad_parse_run(db, parse_run_id)
    if run is None:
        return None
    layers = list_cad_layers(db, parse_run_id, audit=False)
    candidates = list_cad_reference_candidates(db, parse_run_id)
    findings = list(
        db.scalars(
            select(models.CadReviewFinding).where(
                models.CadReviewFinding.parse_run_id == parse_run_id
            )
        ).all()
    )

    layers_by_category: dict[str, int] = {}
    for layer in layers:
        layers_by_category[layer.review_category] = (
            layers_by_category.get(layer.review_category, 0) + 1
        )
    references_by_type: dict[str, int] = {}
    references_by_confidence: dict[str, int] = {}
    for candidate in candidates:
        references_by_type[candidate.reference_type] = (
            references_by_type.get(candidate.reference_type, 0) + 1
        )
        references_by_confidence[candidate.confidence_label] = (
            references_by_confidence.get(candidate.confidence_label, 0) + 1
        )
    findings_by_type: dict[str, int] = {}
    for finding in findings:
        findings_by_type[finding.finding_type] = (
            findings_by_type.get(finding.finding_type, 0) + 1
        )

    if audit:
        _audit(
            db,
            project_id=run.project_id,
            event_type="cad_parse_summary_viewed",
            related_entity_type="cad_parse_run",
            related_entity_id=parse_run_id,
            description="CAD parse summary viewed.",
            actor_type="reviewer",
            metadata={"parse_run_id": parse_run_id},
        )
        db.commit()

    return {
        "parse_run_id": parse_run_id,
        "cad_file_id": run.cad_file_id,
        "project_id": run.project_id,
        "status": run.status,
        "entity_count": run.entity_count,
        "layer_count": run.layer_count,
        "block_count": run.block_count,
        "text_count": run.text_count,
        "warning_count": run.warning_count,
        "reference_candidate_count": len(candidates),
        "finding_count": len(findings),
        "layers_by_category": layers_by_category,
        "references_by_type": references_by_type,
        "references_by_confidence": references_by_confidence,
        "findings_by_type": findings_by_type,
        "limitations_note": run.limitations_note,
    }


def compare_cad_references_to_plan_sheets(
    db: Session, parse_run_id: str
) -> dict | None:
    """Compare extracted sheet and detail references to seeded plan sheets.

    Recomputes matches against the current plan sheets, ensures a missing-match
    finding exists for each unmatched sheet or detail reference (idempotent), and
    returns the comparison view. Writes a cad_reference_comparison_run audit
    event.
    """

    run = get_cad_parse_run(db, parse_run_id)
    if run is None:
        return None
    sheet_map = _seeded_sheet_map(db, run.project_id)
    sheet_number_by_id = {
        s.sheet_id: s.sheet_number
        for s in plan_sheet_service.list_plan_sheets(db, run.project_id)
    }
    candidates = [
        c
        for c in list_cad_reference_candidates(db, parse_run_id)
        if c.reference_type in {"sheet_reference", "detail_reference"}
    ]
    # Any candidate that already has a finding (from parse time or a prior
    # comparison) is skipped, so a comparison never double-flags a reference.
    existing_finding_candidate_ids = {
        f.source_reference_candidate_id
        for f in db.scalars(
            select(models.CadReviewFinding).where(
                models.CadReviewFinding.parse_run_id == parse_run_id
            )
        ).all()
        if f.source_reference_candidate_id is not None
    }

    rows = []
    matched_count = 0
    new_findings: list[models.CadReviewFinding] = []
    for candidate in candidates:
        matched_id = sheet_map.get(candidate.normalized_reference)
        candidate.matched_plan_sheet_id = matched_id
        if matched_id:
            matched_count += 1
            candidate.confidence_label = "high"
            candidate.match_reason = (
                f"{candidate.normalized_reference} matches seeded plan sheet."
            )
            candidate.requires_human_review = False
        else:
            if candidate.confidence_label != "needs_human_review":
                candidate.confidence_label = "low"
            candidate.requires_human_review = True
            if candidate.candidate_id not in existing_finding_candidate_ids:
                new_findings.append(
                    _create_finding(
                        db,
                        run=run,
                        finding_type="missing_plan_sheet_match",
                        title=(
                            f"Reference {candidate.reference_text} has no plan "
                            "sheet match"
                        ),
                        description=(
                            f"Reference {candidate.reference_text} has no matching "
                            "seeded plan sheet. Reviewer confirmation needed."
                        ),
                        severity="medium",
                        source_reference_candidate_id=candidate.candidate_id,
                    )
                )
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "reference_text": candidate.reference_text,
                "normalized_reference": candidate.normalized_reference,
                "reference_type": candidate.reference_type,
                "matched_plan_sheet_id": matched_id,
                "matched_sheet_number": sheet_number_by_id.get(matched_id)
                if matched_id
                else None,
                "confidence_label": candidate.confidence_label,
                "match_reason": candidate.match_reason,
            }
        )

    all_findings = list(
        db.scalars(
            select(models.CadReviewFinding).where(
                models.CadReviewFinding.parse_run_id == parse_run_id
            )
        ).all()
    )

    _audit(
        db,
        project_id=run.project_id,
        event_type="cad_reference_comparison_run",
        related_entity_type="cad_parse_run",
        related_entity_id=parse_run_id,
        description="CAD reference comparison to plan sheets run.",
        actor_type="reviewer",
        metadata={
            "parse_run_id": parse_run_id,
            "matched_count": matched_count,
            "unmatched_count": len(candidates) - matched_count,
        },
    )
    db.commit()

    return {
        "parse_run_id": parse_run_id,
        "project_id": run.project_id,
        "total_candidates": len(candidates),
        "matched_count": matched_count,
        "unmatched_count": len(candidates) - matched_count,
        "rows": rows,
        "findings": all_findings,
        "note": CONTEXT_NOTE,
    }


def get_cad_file_review_context(db: Session, cad_file_id: str) -> dict | None:
    """Return the CAD file with its latest parse run, summary, and findings.

    Read side effect: writes a cad_review_context_viewed audit event.
    """

    cad_file = get_cad_file(db, cad_file_id)
    if cad_file is None:
        return None
    run = db.scalars(
        select(models.CadParseRun)
        .where(models.CadParseRun.cad_file_id == cad_file_id)
        .order_by(models.CadParseRun.started_at.desc())
    ).first()

    summary = None
    layers: list = []
    candidates: list = []
    findings: list = []
    if run is not None:
        summary = get_cad_parse_summary(db, run.parse_run_id, audit=False)
        layers = list_cad_layers(db, run.parse_run_id, audit=False)
        candidates = list_cad_reference_candidates(db, run.parse_run_id)
        findings = list(
            db.scalars(
                select(models.CadReviewFinding).where(
                    models.CadReviewFinding.parse_run_id == run.parse_run_id
                )
            ).all()
        )

    _audit(
        db,
        project_id=cad_file.project_id,
        event_type="cad_review_context_viewed",
        related_entity_type="cad_file",
        related_entity_id=cad_file_id,
        description="CAD file review context viewed.",
        actor_type="reviewer",
        metadata={"cad_file_id": cad_file_id},
    )
    db.commit()

    return {
        "cad_file": cad_file,
        "parse_run": run,
        "summary": summary,
        "layers": layers,
        "reference_candidates": candidates,
        "findings": findings,
        "note": CONTEXT_NOTE,
    }


def _latest_parse_run(
    db: Session, cad_file_id: str
) -> models.CadParseRun | None:
    return db.scalars(
        select(models.CadParseRun)
        .where(models.CadParseRun.cad_file_id == cad_file_id)
        .order_by(models.CadParseRun.started_at.desc())
    ).first()


def _queue_status_for(
    cad_file: models.CadFileUpload, run: models.CadParseRun | None
) -> str:
    """Derive the parse queue status for a CAD file from its latest parse run.

    A status of "failed" means the parser could not read the file (a technical
    parse failure), not an engineering failure or a final decision about the plan.
    """

    if run is None:
        if cad_file.validation_status == "needs_human_review":
            return "needs_human_review"
        return "queued"
    if run.status == "started":
        return "parsing"
    if run.status in ALLOWED_CAD_QUEUE_STATUSES:
        return run.status
    return "queued"


def get_cad_parse_queue(db: Session, project_id: str) -> list[dict]:
    """Return the parse queue for a project: one row per uploaded CAD file.

    Each row carries the upload and validation state, the derived queue status,
    and the latest parse run summary so a reviewer can see files needing parse,
    files being parsed, parse failures, and runs needing human review.

    Read side effect: writes a cad_parse_queue_viewed audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)

    files = list_cad_files(db, project_id)
    rows: list[dict] = []
    for cad_file in files:
        run = _latest_parse_run(db, cad_file.cad_file_id)
        queue_status = _queue_status_for(cad_file, run)
        finding_count = 0
        if run is not None:
            finding_count = len(
                list(
                    db.scalars(
                        select(models.CadReviewFinding).where(
                            models.CadReviewFinding.parse_run_id
                            == run.parse_run_id
                        )
                    ).all()
                )
            )
        rows.append(
            {
                "cad_file_id": cad_file.cad_file_id,
                "project_id": project_id,
                "file_name": cad_file.original_file_name or cad_file.file_name,
                "upload_source": cad_file.upload_source,
                "upload_status": cad_file.upload_status,
                "validation_status": cad_file.validation_status,
                "validation_message": cad_file.validation_message,
                "queue_status": queue_status,
                "parse_run_id": run.parse_run_id if run else None,
                "parse_status": run.status if run else None,
                "warning_count": run.warning_count if run else 0,
                "error_message": run.error_message if run else None,
                "finding_count": finding_count,
                "parse_requested_at": cad_file.parse_requested_at,
                "parse_completed_at": cad_file.parse_completed_at,
                "requires_human_review": queue_status
                in {"needs_human_review", "failed"},
            }
        )

    _audit(
        db,
        project_id=project_id,
        event_type="cad_parse_queue_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="CAD parse queue viewed.",
        actor_type="reviewer",
        metadata={"file_count": len(rows)},
    )
    db.commit()
    return rows


def get_cad_intake_dashboard(db: Session, project_id: str) -> dict:
    """Return a CAD intake dashboard summary for a project.

    Counts uploaded files, queue statuses, validation statuses, parse runs by
    status, CAD findings, and unpromoted versus promoted findings. Read side
    effect: writes a cad_intake_dashboard_viewed audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)

    files = list_cad_files(db, project_id)
    queue_status_counts: dict[str, int] = {}
    validation_status_counts: dict[str, int] = {}
    files_needing_parse = 0
    files_with_parse_failures = 0
    for cad_file in files:
        run = _latest_parse_run(db, cad_file.cad_file_id)
        queue_status = _queue_status_for(cad_file, run)
        queue_status_counts[queue_status] = (
            queue_status_counts.get(queue_status, 0) + 1
        )
        validation = cad_file.validation_status or "unknown"
        validation_status_counts[validation] = (
            validation_status_counts.get(validation, 0) + 1
        )
        if queue_status in {"queued", "needs_human_review"}:
            files_needing_parse += 1
        if queue_status == "failed":
            files_with_parse_failures += 1

    parse_runs = list_cad_parse_runs(db, project_id)
    parse_status_counts: dict[str, int] = {}
    for run in parse_runs:
        parse_status_counts[run.status] = (
            parse_status_counts.get(run.status, 0) + 1
        )
    parse_runs_needing_human_review = sum(
        1
        for run in parse_runs
        if run.status in {"needs_human_review", "failed", "completed_with_warnings"}
    )

    all_findings = list_cad_review_findings(db, project_id)
    unpromoted = [
        f
        for f in all_findings
        if f.linked_workflow_item_id is None
        and not f.promoted_to_workflow
        and f.status != "excluded_from_packet"
    ]
    promoted_count = sum(
        1
        for f in all_findings
        if f.linked_workflow_item_id is not None or f.promoted_to_workflow
    )

    _audit(
        db,
        project_id=project_id,
        event_type="cad_intake_dashboard_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="CAD intake dashboard viewed.",
        actor_type="reviewer",
        metadata={"file_count": len(files)},
    )
    db.commit()

    return {
        "project_id": project_id,
        "total_files": len(files),
        "files_needing_parse": files_needing_parse,
        "files_with_parse_failures": files_with_parse_failures,
        "parse_runs_needing_human_review": parse_runs_needing_human_review,
        "total_findings": len(all_findings),
        "unpromoted_findings_count": len(unpromoted),
        "promoted_findings_count": promoted_count,
        "queue_status_counts": queue_status_counts,
        "validation_status_counts": validation_status_counts,
        "parse_status_counts": parse_status_counts,
        "limitations_note": LIMITATIONS_NOTE,
    }
