"""Phase 14 reviewer command center and project health dashboard service.

This service aggregates the existing review-support data across all phases into a
single operational view for a human reviewer: a command center snapshot, project
health metrics, reviewer attention items with a recommended next step, a project
timeline of meaningful events, review readiness checks, reviewer notes, next
steps, and module links into the existing modules.

The dashboard organizes review-support work and links into existing modules
rather than replacing them. It does not approve plans, certify compliance, stamp
drawings, verify CAD, validate design, declare a project safe, close or resolve
issues, or make final engineering decisions. ready_for_human_review means an area
is organized enough for human review, never that it is complete, passed, or
approved. There is no action called approve.

Read side effects: get_project_command_center, get_latest_command_center_snapshot,
get_project_health_metrics, get_reviewer_attention_items, get_project_timeline,
get_review_readiness_checks, get_dashboard_reviewer_notes, get_reviewer_next_steps,
get_project_module_links, and get_project_health_summary each write an audit event
recording reviewer access. This is intentional so the decision history shows
reviewer access.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import ALLOWED_ATTENTION_ITEM_STATUSES
from app.db import models
from app.services import review_cycle_service

LIMITATIONS_NOTE = (
    "The command center aggregates review-support data and links into existing "
    "modules. It does not approve plans, certify compliance, verify CAD, validate "
    "design, declare a project safe, or close or resolve issues. All statuses are "
    "review-support statuses, not final engineering decisions."
)

# Deep-link routes into existing modules.
ROUTE_WORKFLOW = "/workflow-board"
ROUTE_CAD_INTAKE = "/cad-intake"
ROUTE_CAD_REVIEW = "/cad-review"
ROUTE_REVIEW_CYCLES = "/review-cycles"
ROUTE_RESPONSE = "/response-package"
ROUTE_PACKET = "/review-packet"
ROUTE_SHEETS = "/plan-sheets"
ROUTE_SHEET_VIEWER = "/sheet-viewer"
ROUTE_DOCUMENTS = "/documents"
ROUTE_CHECKLIST = "/checklist"


class CommandCenterError(Exception):
    """Raised when a command center operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


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
            audit_event_id=f"audit_cc_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type="reviewer",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def _require_project(db: Session, project_id: str) -> None:
    if db.get(models.Project, project_id) is None:
        raise CommandCenterError("Project not found.", status_code=404)


# ---------------------------------------------------------------------------
# Data gathering (queried directly to avoid other services' read audit writes)
# ---------------------------------------------------------------------------


def _gather(db: Session, project_id: str) -> dict:
    def q(model, *where):
        stmt = select(model).where(model.project_id == project_id)
        for clause in where:
            stmt = stmt.where(clause)
        return list(db.scalars(stmt).all())

    workflow_items = q(models.WorkflowItem)
    documents = q(models.Document)
    checklist_items = q(models.ChecklistItem)
    cad_files = q(models.CadFileUpload)
    cad_parse_runs = q(models.CadParseRun)
    cad_findings = q(models.CadReviewFinding)
    review_cycles = q(models.ReviewCycle)
    resubmittals = q(models.ResubmittalPackage)
    applicant_responses = q(models.ApplicantResponse)
    mappings = q(models.ApplicantResponseMapping)
    comparison_runs = q(models.RevisionComparisonRun)
    change_records = q(models.RevisionChangeRecord)
    carry_forwards = q(models.IssueCarryForward)
    resolutions = q(models.ResponseResolutionRecord)
    follow_ups = q(models.WorkflowFollowUpRequest)

    latest_package = db.scalars(
        select(models.ResponsePackage)
        .where(models.ResponsePackage.project_id == project_id)
        .order_by(models.ResponsePackage.created_at.desc())
    ).first()
    response_items = []
    if latest_package is not None:
        response_items = list(
            db.scalars(
                select(models.ResponsePackageItem).where(
                    models.ResponsePackageItem.response_package_id
                    == latest_package.response_package_id
                )
            ).all()
        )

    packets = q(models.ReviewPacket)
    plan_sheets = q(models.PlanSheet)
    plan_consistency = q(models.PlanConsistencyFinding)
    sheet_hotspots = q(models.PlanSheetHotspot)

    active_cycle = review_cycle_service._active_cycle(db, project_id)
    next_prep = None
    if active_cycle is not None:
        next_prep = db.scalars(
            select(models.NextCyclePreparation).where(
                models.NextCyclePreparation.review_cycle_id
                == active_cycle.review_cycle_id
            )
        ).first()

    mapped_response_ids = {m.applicant_response_id for m in mappings}
    return {
        "workflow_items": workflow_items,
        "documents": documents,
        "checklist_items": checklist_items,
        "cad_files": cad_files,
        "cad_parse_runs": cad_parse_runs,
        "cad_findings": cad_findings,
        "review_cycles": review_cycles,
        "resubmittals": resubmittals,
        "applicant_responses": applicant_responses,
        "mappings": mappings,
        "mapped_response_ids": mapped_response_ids,
        "comparison_runs": comparison_runs,
        "change_records": change_records,
        "carry_forwards": carry_forwards,
        "resolutions": resolutions,
        "follow_ups": follow_ups,
        "response_items": response_items,
        "packets": packets,
        "plan_sheets": plan_sheets,
        "plan_consistency": plan_consistency,
        "sheet_hotspots": sheet_hotspots,
        "active_cycle": active_cycle,
        "next_prep": next_prep,
    }


def _unpromoted_findings(data: dict) -> list:
    return [
        f
        for f in data["cad_findings"]
        if f.linked_workflow_item_id is None
        and not f.promoted_to_workflow
        and f.status != "excluded_from_packet"
    ]


def _open_carry_forwards(data: dict) -> list:
    return [
        c
        for c in data["carry_forwards"]
        if c.carried_forward_status
        in {"carried_forward", "needs_follow_up", "needs_more_information"}
    ]


def _unmapped_responses(data: dict) -> list:
    return [
        r
        for r in data["applicant_responses"]
        if r.applicant_response_id not in data["mapped_response_ids"]
    ]


def _low_confidence_mappings(data: dict) -> list:
    return [
        m
        for m in data["mappings"]
        if m.mapping_confidence in {"low", "needs_human_review"}
    ]


def _resubmittals_needing_comparison(data: dict) -> list:
    compared_ids = {
        run.resubmittal_package_id
        for run in data["comparison_runs"]
        if run.resubmittal_package_id is not None
    }
    return [
        p
        for p in data["resubmittals"]
        if p.status in {"received", "intake_review", "ready_for_comparison"}
        and p.resubmittal_package_id not in compared_ids
    ]


def _comparisons_needing_review(data: dict) -> list:
    by_run: dict[str, int] = {}
    for record in data["change_records"]:
        needs = record.reviewer_status in {
            "needs_follow_up",
            "needs_more_information",
        } or (record.change_type == "carried_forward" and record.requires_human_review)
        if needs:
            by_run[record.comparison_run_id] = by_run.get(record.comparison_run_id, 0) + 1
    return [
        (run, by_run[run.comparison_run_id])
        for run in data["comparison_runs"]
        if by_run.get(run.comparison_run_id, 0) > 0
    ]


def _evidence_gap_items(data: dict) -> list:
    return [
        item
        for item in data["checklist_items"]
        if item.expected_status_for_brookside_meadows
        in {"missing", "conflicting", "unclear"}
    ]


def _open_follow_ups(data: dict) -> list:
    return [
        f
        for f in data["follow_ups"]
        if f.status in {"open", "response_needed"}
    ]


# ---------------------------------------------------------------------------
# Attention item generation
# ---------------------------------------------------------------------------


def _build_attention_items(
    data: dict, snapshot_id: str, project_id: str, prior_status: dict
) -> list[models.ReviewerAttentionItem]:
    items: list[models.ReviewerAttentionItem] = []

    def add(
        *,
        title: str,
        description: str,
        attention_type: str,
        severity: str,
        source_module: str,
        source_type: str,
        source_id: str | None,
        target_route: str,
        recommended_next_step: str,
    ) -> None:
        status = prior_status.get((source_type, source_id), "open")
        items.append(
            models.ReviewerAttentionItem(
                attention_item_id=f"att_{_short()}",
                snapshot_id=snapshot_id,
                project_id=project_id,
                title=title,
                description=description,
                attention_type=attention_type,
                severity=severity,
                source_module=source_module,
                source_type=source_type,
                source_id=source_id,
                target_route=target_route,
                recommended_next_step=recommended_next_step,
                status=status,
                requires_human_review=True,
            )
        )

    # Workflow items needing follow-up or more information.
    for item in data["workflow_items"]:
        if item.status not in {"needs_follow_up", "needs_more_information"}:
            continue
        add(
            title=item.title,
            description=(
                f"Workflow item is in '{item.status.replace('_', ' ')}' and needs "
                "reviewer follow-up."
            ),
            attention_type="workflow_item_needs_follow_up",
            severity="medium" if item.status == "needs_follow_up" else "high",
            source_module="workflow_board",
            source_type="workflow_item",
            source_id=item.workflow_item_id,
            target_route=ROUTE_WORKFLOW,
            recommended_next_step=(
                "Open the workflow item and record the follow-up or requested "
                "information."
            ),
        )

    # Workflow items ready for handoff (summary).
    handoff = [i for i in data["workflow_items"] if i.status == "ready_for_handoff"]
    if handoff:
        add(
            title=f"{len(handoff)} item(s) ready for handoff review",
            description=(
                "Workflow items are marked ready for handoff and need a human "
                "review before handing the organized evidence to a licensed "
                "Professional Engineer."
            ),
            attention_type="ready_for_handoff_review",
            severity="medium",
            source_module="workflow_board",
            source_type="workflow_handoff",
            source_id=project_id,
            target_route=ROUTE_WORKFLOW,
            recommended_next_step="Review the ready-for-handoff items on the board.",
        )

    # Open follow-up requests (summary).
    open_follow_ups = _open_follow_ups(data)
    if open_follow_ups:
        add(
            title=f"{len(open_follow_ups)} open follow-up request(s)",
            description="Follow-up requests are open and awaiting a response.",
            attention_type="workflow_item_needs_follow_up",
            severity="medium",
            source_module="workflow_board",
            source_type="follow_up_requests",
            source_id=project_id,
            target_route=ROUTE_WORKFLOW,
            recommended_next_step="Review open follow-up requests on the board.",
        )

    # CAD files with a technical parse failure.
    for cad_file in data["cad_files"]:
        if cad_file.upload_status != "parse_failed":
            continue
        add(
            title=f"DXF parse failed: {cad_file.original_file_name or cad_file.file_name}",
            description=(
                "The DXF parser could not read this file. This is a technical "
                "parse failure, not an engineering failure."
            ),
            attention_type="cad_parse_needs_review",
            severity="high",
            source_module="cad_intake",
            source_type="cad_file",
            source_id=cad_file.cad_file_id,
            target_route=ROUTE_CAD_INTAKE,
            recommended_next_step="Re-export or repair the DXF and request the parse again.",
        )

    # CAD parse runs needing human review.
    for run in data["cad_parse_runs"]:
        if run.status != "needs_human_review":
            continue
        add(
            title="CAD parse run needs human review",
            description="A DXF parse run is flagged for human review.",
            attention_type="cad_parse_needs_review",
            severity="medium",
            source_module="cad_intake",
            source_type="cad_parse_run",
            source_id=run.parse_run_id,
            target_route=ROUTE_CAD_INTAKE,
            recommended_next_step="Open the parse run and confirm the extracted metadata.",
        )

    # Unpromoted CAD findings (summary).
    unpromoted = _unpromoted_findings(data)
    if unpromoted:
        add(
            title=f"{len(unpromoted)} unpromoted CAD finding(s)",
            description=(
                "CAD review findings have not yet been promoted to the workflow "
                "board and still need review."
            ),
            attention_type="cad_finding_unpromoted",
            severity="medium",
            source_module="cad_intake",
            source_type="cad_unpromoted_findings",
            source_id=project_id,
            target_route=ROUTE_CAD_INTAKE,
            recommended_next_step="Review the unpromoted CAD findings and promote those that need tracking.",
        )

    # Applicant responses without a mapping.
    for response in _unmapped_responses(data):
        add(
            title=f"Applicant response needs mapping: {response.response_topic}",
            description=(
                "An applicant response has not been mapped to a prior response or "
                "workflow item."
            ),
            attention_type="applicant_response_needs_mapping",
            severity="medium",
            source_module="review_cycles",
            source_type="applicant_response",
            source_id=response.applicant_response_id,
            target_route=ROUTE_REVIEW_CYCLES,
            recommended_next_step="Map the applicant response to a prior item or suggest mappings.",
        )

    # Low-confidence applicant response mappings.
    for mapping in _low_confidence_mappings(data):
        add(
            title="Low-confidence applicant response mapping",
            description=(
                f"A mapping suggestion has '{mapping.mapping_confidence.replace('_', ' ')}' "
                "confidence and needs reviewer confirmation."
            ),
            attention_type="applicant_response_needs_mapping",
            severity="low",
            source_module="review_cycles",
            source_type="applicant_response_mapping",
            source_id=mapping.mapping_id,
            target_route=ROUTE_REVIEW_CYCLES,
            recommended_next_step="Confirm or correct the suggested mapping.",
        )

    # Resubmittals needing comparison.
    for package in _resubmittals_needing_comparison(data):
        add(
            title=f"Resubmittal awaiting comparison: {package.package_name}",
            description=(
                "A resubmittal has been recorded but has no revision comparison "
                "against the previous round yet."
            ),
            attention_type="resubmittal_needs_comparison",
            severity="medium",
            source_module="review_cycles",
            source_type="resubmittal_package",
            source_id=package.resubmittal_package_id,
            target_route=ROUTE_REVIEW_CYCLES,
            recommended_next_step="Run a DXF revision comparison for the resubmittal.",
        )

    # Revision changes needing review (per comparison run).
    for run, count in _comparisons_needing_review(data):
        add(
            title=f"{count} revision change(s) need review",
            description=(
                "Revision changes from a DXF metadata comparison still need "
                "reviewer attention."
            ),
            attention_type="revision_change_needs_review",
            severity="medium",
            source_module="review_cycles",
            source_type="revision_comparison_run",
            source_id=run.comparison_run_id,
            target_route=ROUTE_REVIEW_CYCLES,
            recommended_next_step="Review the revision changes and record resolution statuses.",
        )

    # Carry-forward items (summary).
    open_cf = _open_carry_forwards(data)
    if open_cf:
        add(
            title=f"{len(open_cf)} carry-forward item(s) need review",
            description="Unresolved items have been carried forward and need review.",
            attention_type="carry_forward_item",
            severity="medium",
            source_module="review_cycles",
            source_type="carry_forward",
            source_id=project_id,
            target_route=ROUTE_REVIEW_CYCLES,
            recommended_next_step="Review carried-forward items and record resolution statuses.",
        )

    # Response package items needing revision.
    for item in data["response_items"]:
        if item.status != "needs_revision":
            continue
        add(
            title=f"Response item needs revision: {item.title}",
            description="A response package item is marked needs revision.",
            attention_type="response_item_needs_revision",
            severity="medium",
            source_module="response_package",
            source_type="response_package_item",
            source_id=item.item_id,
            target_route=ROUTE_RESPONSE,
            recommended_next_step="Revise the draft response item text.",
        )

    # Next-cycle preparation needing human review.
    prep = data["next_prep"]
    if prep is not None and prep.status == "needs_human_review":
        add(
            title="Next-cycle preparation needs human review",
            description="The next-cycle preparation summary is flagged for human review.",
            attention_type="carry_forward_item",
            severity="low",
            source_module="review_cycles",
            source_type="next_cycle_preparation",
            source_id=prep.next_cycle_preparation_id,
            target_route=ROUTE_REVIEW_CYCLES,
            recommended_next_step="Review the next-cycle preparation summary.",
        )

    # Evidence gaps from checklist items (summary).
    gaps = _evidence_gap_items(data)
    if gaps:
        add(
            title=f"{len(gaps)} checklist item(s) show an evidence gap",
            description=(
                "Checklist items have a missing, conflicting, or unclear expected "
                "status and need reviewer attention."
            ),
            attention_type="evidence_gap",
            severity="medium",
            source_module="checklist",
            source_type="evidence_gap",
            source_id=project_id,
            target_route=ROUTE_CHECKLIST,
            recommended_next_step="Review the checklist items with evidence gaps.",
        )

    return items


# ---------------------------------------------------------------------------
# Health metrics
# ---------------------------------------------------------------------------


def _severity_for_count(count: int, *, high: int = 3) -> str:
    if count == 0:
        return "info"
    if count >= high:
        return "high"
    return "medium"


def _build_metrics(
    data: dict, snapshot_id: str, project_id: str
) -> list[models.ProjectHealthMetric]:
    metrics: list[models.ProjectHealthMetric] = []

    def add(metric_type, label, value, severity, source_module, source_route):
        metrics.append(
            models.ProjectHealthMetric(
                metric_id=f"hm_{_short()}",
                snapshot_id=snapshot_id,
                project_id=project_id,
                metric_type=metric_type,
                label=label,
                value=str(value),
                severity=severity,
                source_module=source_module,
                source_route=source_route,
                requires_human_review=True,
            )
        )

    workflow_attention = len(
        [
            i
            for i in data["workflow_items"]
            if i.status in {"needs_follow_up", "needs_more_information"}
        ]
    )
    add(
        "workflow_status_count",
        "Workflow items needing attention",
        workflow_attention,
        _severity_for_count(workflow_attention),
        "workflow_board",
        ROUTE_WORKFLOW,
    )

    response_revision = len(
        [i for i in data["response_items"] if i.status == "needs_revision"]
    )
    add(
        "response_package_status",
        "Response items needing revision",
        response_revision,
        _severity_for_count(response_revision),
        "response_package",
        ROUTE_RESPONSE,
    )

    add(
        "cad_intake_status",
        "CAD files in intake",
        len(data["cad_files"]),
        "info",
        "cad_intake",
        ROUTE_CAD_INTAKE,
    )

    parse_failures = len(
        [c for c in data["cad_files"] if c.upload_status == "parse_failed"]
    )
    add(
        "cad_intake_status",
        "CAD parse failures",
        parse_failures,
        "high" if parse_failures else "info",
        "cad_intake",
        ROUTE_CAD_INTAKE,
    )

    unpromoted = len(_unpromoted_findings(data))
    add(
        "evidence_gap",
        "Unpromoted CAD findings",
        unpromoted,
        _severity_for_count(unpromoted),
        "cad_intake",
        ROUTE_CAD_INTAKE,
    )

    add(
        "applicant_response_mapping",
        "Applicant responses needing mapping",
        len(_unmapped_responses(data)),
        _severity_for_count(len(_unmapped_responses(data))),
        "review_cycles",
        ROUTE_REVIEW_CYCLES,
    )

    needing_comparison = len(_resubmittals_needing_comparison(data))
    add(
        "resubmittal_status",
        "Resubmittals awaiting comparison",
        needing_comparison,
        _severity_for_count(needing_comparison),
        "review_cycles",
        ROUTE_REVIEW_CYCLES,
    )

    revision_needing = sum(c for _run, c in _comparisons_needing_review(data))
    add(
        "revision_comparison_status",
        "Revision changes needing review",
        revision_needing,
        _severity_for_count(revision_needing),
        "review_cycles",
        ROUTE_REVIEW_CYCLES,
    )

    open_cf = len(_open_carry_forwards(data))
    add(
        "carry_forward_status",
        "Carry-forward items",
        open_cf,
        _severity_for_count(open_cf),
        "review_cycles",
        ROUTE_REVIEW_CYCLES,
    )

    open_resolutions = len(
        [
            r
            for r in data["resolutions"]
            if r.status in {"still_open", "needs_more_information", "carried_forward"}
        ]
    )
    add(
        "review_readiness",
        "Open resolution items",
        open_resolutions,
        _severity_for_count(open_resolutions),
        "review_cycles",
        ROUTE_REVIEW_CYCLES,
    )

    return metrics


# ---------------------------------------------------------------------------
# Readiness checks
# ---------------------------------------------------------------------------


def _readiness_status(source_count: int, blocker_count: int) -> str:
    if source_count == 0:
        return "not_started"
    if blocker_count > 0:
        return "needs_attention"
    return "ready_for_human_review"


def _build_readiness_checks(
    data: dict, snapshot_id: str, project_id: str
) -> list[models.ReviewReadinessCheck]:
    checks: list[models.ReviewReadinessCheck] = []

    def add(
        check_type,
        label,
        description,
        status,
        source_module,
        source_count,
        blocker_count,
        recommended_next_step,
    ):
        checks.append(
            models.ReviewReadinessCheck(
                readiness_check_id=f"rc_{_short()}",
                snapshot_id=snapshot_id,
                project_id=project_id,
                check_type=check_type,
                label=label,
                description=description,
                status=status,
                source_module=source_module,
                source_count=source_count,
                blocker_count=blocker_count,
                recommended_next_step=recommended_next_step,
                requires_human_review=True,
            )
        )

    gaps = len(_evidence_gap_items(data))
    add(
        "documents_reviewed",
        "Documents reviewed for gaps",
        "Checklist items reviewed for missing, conflicting, or unclear evidence.",
        _readiness_status(len(data["checklist_items"]), gaps),
        "checklist",
        len(data["checklist_items"]),
        gaps,
        "Review checklist items with evidence gaps.",
    )

    parse_failures = len(
        [c for c in data["cad_files"] if c.upload_status == "parse_failed"]
    )
    add(
        "cad_intake_reviewed",
        "CAD intake reviewed",
        "Uploaded DXF files parsed and reviewed for technical parse failures.",
        _readiness_status(len(data["cad_files"]), parse_failures),
        "cad_intake",
        len(data["cad_files"]),
        parse_failures,
        "Review CAD intake and resolve any technical parse failures.",
    )

    unpromoted = len(_unpromoted_findings(data))
    add(
        "cad_findings_reviewed",
        "Unpromoted CAD findings reviewed",
        "CAD review findings reviewed and promoted where they need tracking.",
        _readiness_status(len(data["cad_findings"]), unpromoted),
        "cad_intake",
        len(data["cad_findings"]),
        unpromoted,
        "Review and promote unpromoted CAD findings.",
    )

    untriaged = len(
        [i for i in data["workflow_items"] if i.status in {"draft", "needs_triage"}]
    )
    add(
        "workflow_triaged",
        "Workflow items triaged",
        "Workflow board items triaged out of the initial draft state.",
        _readiness_status(len(data["workflow_items"]), untriaged),
        "workflow_board",
        len(data["workflow_items"]),
        untriaged,
        "Triage workflow items still in draft.",
    )

    unmapped = len(_unmapped_responses(data))
    add(
        "applicant_responses_mapped",
        "Applicant responses mapped",
        "Applicant responses mapped to prior response or workflow items.",
        _readiness_status(len(data["applicant_responses"]), unmapped),
        "review_cycles",
        len(data["applicant_responses"]),
        unmapped,
        "Map remaining applicant responses.",
    )

    revision_needing = sum(c for _run, c in _comparisons_needing_review(data))
    add(
        "revision_comparison_reviewed",
        "Revision comparison reviewed",
        "DXF metadata revision changes reviewed across rounds.",
        _readiness_status(len(data["comparison_runs"]), revision_needing),
        "review_cycles",
        len(data["comparison_runs"]),
        revision_needing,
        "Review revision changes needing attention.",
    )

    open_cf = len(_open_carry_forwards(data))
    add(
        "carry_forward_reviewed",
        "Carry-forward items reviewed",
        "Carried-forward items reviewed and given a resolution status.",
        _readiness_status(len(data["carry_forwards"]), open_cf),
        "review_cycles",
        len(data["carry_forwards"]),
        open_cf,
        "Review carried-forward items.",
    )

    package_items = len(data["response_items"])
    revision_items = len(
        [i for i in data["response_items"] if i.status == "needs_revision"]
    )
    add(
        "response_package_prepared",
        "Response package prepared",
        "A draft response package has been prepared for human review.",
        _readiness_status(package_items, revision_items),
        "response_package",
        package_items,
        revision_items,
        "Prepare or revise the response package.",
    )

    # Human review signoff is always required and is never marked complete.
    add(
        "human_review_signoff",
        "Human review signoff still required",
        "A licensed Professional Engineer must review before any final decision. "
        "Civil Engineer AI never approves, certifies, or finalizes the work.",
        "ready_for_human_review",
        "human_review",
        1,
        1,
        "Route the organized review-support evidence to a licensed Professional Engineer.",
    )

    return checks


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


def _build_timeline_events(
    data: dict, project_id: str
) -> list[models.ProjectTimelineEvent]:
    events: list[models.ProjectTimelineEvent] = []

    def add(event_type, title, description, module, source_type, source_id, when, route):
        if when is None:
            return
        events.append(
            models.ProjectTimelineEvent(
                timeline_event_id=f"tl_{_short()}",
                project_id=project_id,
                event_type=event_type,
                event_title=title,
                event_description=description,
                source_module=module,
                source_type=source_type,
                source_id=source_id,
                event_time=when,
                target_route=route,
                requires_human_review=False,
            )
        )

    for packet in data["packets"]:
        add(
            "review_packet_generated",
            "Review packet generated",
            f"Review-support packet '{packet.title}' generated.",
            "review_packet",
            "review_packet",
            packet.packet_id,
            packet.created_at,
            ROUTE_PACKET,
        )

    workflow_items = sorted(
        data["workflow_items"], key=lambda i: i.created_at
    )
    if workflow_items:
        first = workflow_items[0]
        add(
            "workflow_item_created",
            "Workflow board generated",
            "Reviewer workflow board generated from review-support items.",
            "workflow_board",
            "workflow_board",
            project_id,
            first.created_at,
            ROUTE_WORKFLOW,
        )

    response_packages = db_response_packages(data)
    for package in response_packages:
        add(
            "response_package_generated",
            "Response package generated",
            f"Draft response package '{package.title}' generated.",
            "response_package",
            "response_package",
            package.response_package_id,
            package.created_at,
            ROUTE_RESPONSE,
        )

    for cad_file in data["cad_files"]:
        add(
            "cad_file_uploaded",
            "CAD file registered",
            f"DXF file '{cad_file.original_file_name or cad_file.file_name}' registered for intake.",
            "cad_intake",
            "cad_file",
            cad_file.cad_file_id,
            cad_file.created_at,
            ROUTE_CAD_INTAKE,
        )

    for run in data["cad_parse_runs"]:
        if run.status in {"completed", "completed_with_warnings"}:
            add(
                "cad_parse_completed",
                "DXF parse run recorded",
                f"DXF parse run finished with {run.entity_count} entities.",
                "cad_intake",
                "cad_parse_run",
                run.parse_run_id,
                run.completed_at or run.started_at,
                ROUTE_CAD_INTAKE,
            )

    for resub in data["resubmittals"]:
        add(
            "resubmittal_received",
            "Resubmittal received",
            f"Resubmittal '{resub.package_name}' received.",
            "review_cycles",
            "resubmittal_package",
            resub.resubmittal_package_id,
            resub.received_at,
            ROUTE_REVIEW_CYCLES,
        )

    for response in data["applicant_responses"]:
        add(
            "applicant_response_received",
            "Applicant response received",
            f"Applicant response on '{response.response_topic}' received.",
            "review_cycles",
            "applicant_response",
            response.applicant_response_id,
            response.created_at,
            ROUTE_REVIEW_CYCLES,
        )

    for run in data["comparison_runs"]:
        add(
            "revision_comparison_completed",
            "Revision comparison recorded",
            f"DXF metadata revision comparison recorded ({run.status.replace('_', ' ')}).",
            "review_cycles",
            "revision_comparison_run",
            run.comparison_run_id,
            run.completed_at or run.started_at,
            ROUTE_REVIEW_CYCLES,
        )

    # One carry-forward event per cycle that has carry-forwards.
    cycles_with_cf: dict[str, datetime] = {}
    for cf in data["carry_forwards"]:
        existing = cycles_with_cf.get(cf.review_cycle_id)
        if existing is None or cf.created_at < existing:
            cycles_with_cf[cf.review_cycle_id] = cf.created_at
    for cycle_id, when in cycles_with_cf.items():
        add(
            "issue_carried_forward",
            "Issues carried forward",
            "Unresolved review-support items carried forward to a later round.",
            "review_cycles",
            "review_cycle_carry_forward",
            cycle_id,
            when,
            ROUTE_REVIEW_CYCLES,
        )

    if data["next_prep"] is not None:
        prep = data["next_prep"]
        add(
            "next_cycle_prepared",
            "Next cycle prepared",
            "A next-cycle preparation summary was generated.",
            "review_cycles",
            "next_cycle_preparation",
            prep.next_cycle_preparation_id,
            prep.created_at,
            ROUTE_REVIEW_CYCLES,
        )

    events.sort(key=lambda e: e.event_time)
    return events


def db_response_packages(data: dict) -> list:
    # Helper kept separate so the timeline reads response packages from the gather
    # set without an extra query path.
    return data.get("response_packages", [])


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


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def get_latest_snapshot_record(
    db: Session, project_id: str
) -> models.ProjectCommandCenterSnapshot | None:
    return db.scalars(
        select(models.ProjectCommandCenterSnapshot)
        .where(models.ProjectCommandCenterSnapshot.project_id == project_id)
        .order_by(models.ProjectCommandCenterSnapshot.generated_at.desc())
    ).first()


def _ensure_snapshot(
    db: Session, project_id: str
) -> models.ProjectCommandCenterSnapshot:
    snapshot = get_latest_snapshot_record(db, project_id)
    if snapshot is None:
        snapshot = generate_command_center_snapshot(db, project_id)
    return snapshot


def get_latest_command_center_snapshot(
    db: Session, project_id: str
) -> models.ProjectCommandCenterSnapshot | None:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_latest_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Latest command center snapshot viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return snapshot


def _metrics_for(db: Session, snapshot_id: str) -> list:
    return list(
        db.scalars(
            select(models.ProjectHealthMetric)
            .where(models.ProjectHealthMetric.snapshot_id == snapshot_id)
            .order_by(models.ProjectHealthMetric.id)
        ).all()
    )


def _attention_for(db: Session, snapshot_id: str, **filters) -> list:
    stmt = select(models.ReviewerAttentionItem).where(
        models.ReviewerAttentionItem.snapshot_id == snapshot_id
    )
    if filters.get("status"):
        stmt = stmt.where(models.ReviewerAttentionItem.status == filters["status"])
    if filters.get("severity"):
        stmt = stmt.where(
            models.ReviewerAttentionItem.severity == filters["severity"]
        )
    if filters.get("source_module"):
        stmt = stmt.where(
            models.ReviewerAttentionItem.source_module == filters["source_module"]
        )
    if filters.get("attention_type"):
        stmt = stmt.where(
            models.ReviewerAttentionItem.attention_type
            == filters["attention_type"]
        )
    stmt = stmt.order_by(models.ReviewerAttentionItem.id)
    return list(db.scalars(stmt).all())


def _readiness_for(db: Session, snapshot_id: str) -> list:
    return list(
        db.scalars(
            select(models.ReviewReadinessCheck)
            .where(models.ReviewReadinessCheck.snapshot_id == snapshot_id)
            .order_by(models.ReviewReadinessCheck.id)
        ).all()
    )


def get_project_health_metrics(db: Session, project_id: str) -> list:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    metrics = _metrics_for(db, snapshot.snapshot_id)
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_metrics_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center health metrics viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return metrics


def get_reviewer_attention_items(
    db: Session,
    project_id: str,
    *,
    status: str | None = None,
    severity: str | None = None,
    source_module: str | None = None,
    attention_type: str | None = None,
) -> list:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    items = _attention_for(
        db,
        snapshot.snapshot_id,
        status=status,
        severity=severity,
        source_module=source_module,
        attention_type=attention_type,
    )
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_attention_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center attention items viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id, "count": len(items)},
    )
    db.commit()
    return items


def update_attention_item_status(
    db: Session,
    attention_item_id: str,
    *,
    status: str,
    reviewer_note: str | None = None,
    reviewer_name: str = "reviewer",
) -> models.ReviewerAttentionItem:
    item = db.scalars(
        select(models.ReviewerAttentionItem).where(
            models.ReviewerAttentionItem.attention_item_id == attention_item_id
        )
    ).first()
    if item is None:
        raise CommandCenterError("Attention item not found.", status_code=404)
    if status not in ALLOWED_ATTENTION_ITEM_STATUSES:
        raise CommandCenterError(
            f"Invalid attention item status '{status}'.", status_code=422
        )
    previous = item.status
    item.status = status
    _audit(
        db,
        project_id=item.project_id,
        event_type="command_center_attention_status_changed",
        related_entity_type="reviewer_attention_item",
        related_entity_id=attention_item_id,
        description=(
            f"Attention item status changed from {previous} to {status} by "
            f"{reviewer_name}."
            + (f" Note: {reviewer_note}" if reviewer_note else "")
        ),
        metadata={"previous_status": previous, "new_status": status},
    )
    db.commit()
    db.refresh(item)
    return item


def get_project_timeline(db: Session, project_id: str) -> list:
    _require_project(db, project_id)
    _ensure_snapshot(db, project_id)
    events = list(
        db.scalars(
            select(models.ProjectTimelineEvent)
            .where(models.ProjectTimelineEvent.project_id == project_id)
            .order_by(models.ProjectTimelineEvent.event_time)
        ).all()
    )
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_timeline_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Command center timeline viewed.",
        metadata={"event_count": len(events)},
    )
    db.commit()
    return events


def get_review_readiness_checks(db: Session, project_id: str) -> list:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    checks = _readiness_for(db, snapshot.snapshot_id)
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_readiness_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center readiness checks viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return checks


def add_dashboard_reviewer_note(
    db: Session,
    project_id: str,
    *,
    note_text: str,
    reviewer_name: str = "reviewer",
    snapshot_id: str | None = None,
    source_context: str | None = None,
) -> models.DashboardReviewerNote:
    _require_project(db, project_id)
    if snapshot_id is None:
        latest = get_latest_snapshot_record(db, project_id)
        snapshot_id = latest.snapshot_id if latest else None
    note = models.DashboardReviewerNote(
        note_id=f"note_{_short()}",
        project_id=project_id,
        snapshot_id=snapshot_id,
        note_text=note_text,
        reviewer_name=reviewer_name,
        source_context=source_context,
        requires_human_review=True,
    )
    db.add(note)
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_note_added",
        related_entity_type="dashboard_reviewer_note",
        related_entity_id=note.note_id,
        description="Dashboard reviewer note added.",
        metadata={"note_id": note.note_id},
    )
    db.commit()
    db.refresh(note)
    return note


def get_dashboard_reviewer_notes(db: Session, project_id: str) -> list:
    _require_project(db, project_id)
    notes = list(
        db.scalars(
            select(models.DashboardReviewerNote)
            .where(models.DashboardReviewerNote.project_id == project_id)
            .order_by(models.DashboardReviewerNote.created_at.desc())
        ).all()
    )
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_notes_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Dashboard reviewer notes viewed.",
        metadata={"note_count": len(notes)},
    )
    db.commit()
    return notes


_SEVERITY_RANK = {
    "needs_human_review": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "info": 0,
}


def get_reviewer_next_steps(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    open_items = _attention_for(db, snapshot.snapshot_id, status="open")
    # One step per attention type, highest severity first.
    by_type: dict[str, models.ReviewerAttentionItem] = {}
    for item in open_items:
        current = by_type.get(item.attention_type)
        if current is None or _SEVERITY_RANK.get(item.severity, 0) > _SEVERITY_RANK.get(
            current.severity, 0
        ):
            by_type[item.attention_type] = item
    ordered = sorted(
        by_type.values(),
        key=lambda i: _SEVERITY_RANK.get(i.severity, 0),
        reverse=True,
    )
    steps = [
        {
            "title": item.title,
            "detail": item.recommended_next_step,
            "severity": item.severity,
            "target_route": item.target_route,
            "source_module": item.source_module,
        }
        for item in ordered[:6]
    ]
    if not steps:
        steps = [
            {
                "title": "Route organized evidence for human review",
                "detail": (
                    "No open attention items. A licensed Professional Engineer "
                    "review is still required before any final decision."
                ),
                "severity": "info",
                "target_route": ROUTE_WORKFLOW,
                "source_module": "human_review",
            }
        ]
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_next_steps_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center next steps viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return {
        "project_id": project_id,
        "snapshot_id": snapshot.snapshot_id,
        "steps": steps,
        "note": (
            "Recommended review-support steps. None of these approves, certifies, "
            "or finalizes the work."
        ),
    }


def get_project_module_links(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    data = _gather(db, project_id)

    def link(module, label, route, description, count):
        return {
            "module": module,
            "label": label,
            "route": route,
            "description": description,
            "count": count,
            "severity": _severity_for_count(count) if count else "info",
        }

    workflow_attention = len(
        [
            i
            for i in data["workflow_items"]
            if i.status in {"needs_follow_up", "needs_more_information"}
        ]
    )
    links = [
        link(
            "project_dashboard",
            "Project Dashboard",
            "/project-dashboard",
            "Unified command center for the project review state.",
            0,
        ),
        link(
            "cad_intake",
            "CAD Intake",
            ROUTE_CAD_INTAKE,
            "Upload, parse, and review DXF files and CAD findings.",
            len(data["cad_files"]),
        ),
        link(
            "review_cycles",
            "Review Cycles",
            ROUTE_REVIEW_CYCLES,
            "Resubmittals, revision comparison, and the response cycle.",
            len(data["resubmittals"]),
        ),
        link(
            "workflow_board",
            "Workflow Board",
            ROUTE_WORKFLOW,
            "Track review-support items through triage to handoff.",
            workflow_attention,
        ),
        link(
            "response_package",
            "Response Package",
            ROUTE_RESPONSE,
            "Draft external review response package.",
            len(
                [i for i in data["response_items"] if i.status == "needs_revision"]
            ),
        ),
        link(
            "review_packet",
            "Review Packet",
            ROUTE_PACKET,
            "Assembled review-support packet with evidence traceability.",
            len(data["packets"]),
        ),
        link(
            "plan_sheets",
            "Plan Sheets",
            ROUTE_SHEETS,
            "Plan sheet index with revisions and missing sheet detection.",
            len(data["plan_sheets"]),
        ),
        link(
            "cad_review",
            "CAD Review",
            ROUTE_CAD_REVIEW,
            "CAD-aware metadata, plan references, and consistency findings.",
            len(data["plan_consistency"]),
        ),
        link(
            "sheet_viewer",
            "Sheet Viewer",
            ROUTE_SHEET_VIEWER,
            "Plan sheet viewer with seeded sheet hotspots.",
            len(data["sheet_hotspots"]),
        ),
    ]
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_module_links_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Command center module links viewed.",
        metadata={"link_count": len(links)},
    )
    db.commit()
    return {
        "project_id": project_id,
        "links": links,
        "note": (
            "The dashboard links into existing modules rather than replacing them."
        ),
    }


def get_project_health_summary(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    readiness = _readiness_for(db, snapshot.snapshot_id)
    readiness_ready = len(
        [c for c in readiness if c.status == "ready_for_human_review"]
    )
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_health_summary_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center health summary viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return {
        "project_id": project_id,
        "snapshot_id": snapshot.snapshot_id,
        "overall_status": snapshot.overall_status,
        "current_review_cycle_id": snapshot.current_review_cycle_id,
        "attention_count": snapshot.attention_count,
        "ready_for_handoff_count": snapshot.ready_for_handoff_count,
        "carry_forward_count": snapshot.carry_forward_count,
        "needs_more_information_count": snapshot.needs_more_information_count,
        "cad_findings_count": snapshot.cad_findings_count,
        "resubmittal_count": snapshot.resubmittal_count,
        "open_follow_up_count": snapshot.open_follow_up_count,
        "response_mapping_gap_count": snapshot.response_mapping_gap_count,
        "revision_change_count": snapshot.revision_change_count,
        "readiness_ready_count": readiness_ready,
        "summary": snapshot.summary,
        "limitations_note": LIMITATIONS_NOTE,
    }


def get_project_command_center(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    metrics = _metrics_for(db, snapshot.snapshot_id)
    attention = _attention_for(db, snapshot.snapshot_id, status="open")
    timeline = list(
        db.scalars(
            select(models.ProjectTimelineEvent)
            .where(models.ProjectTimelineEvent.project_id == project_id)
            .order_by(models.ProjectTimelineEvent.event_time)
        ).all()
    )
    readiness = _readiness_for(db, snapshot.snapshot_id)
    notes = list(
        db.scalars(
            select(models.DashboardReviewerNote)
            .where(models.DashboardReviewerNote.project_id == project_id)
            .order_by(models.DashboardReviewerNote.created_at.desc())
        ).all()
    )

    # Next steps and module links assembled inline (no extra audit writes here).
    open_items = attention
    by_type: dict[str, models.ReviewerAttentionItem] = {}
    for item in open_items:
        current = by_type.get(item.attention_type)
        if current is None or _SEVERITY_RANK.get(item.severity, 0) > _SEVERITY_RANK.get(
            current.severity, 0
        ):
            by_type[item.attention_type] = item
    ordered = sorted(
        by_type.values(),
        key=lambda i: _SEVERITY_RANK.get(i.severity, 0),
        reverse=True,
    )
    steps = [
        {
            "title": item.title,
            "detail": item.recommended_next_step,
            "severity": item.severity,
            "target_route": item.target_route,
            "source_module": item.source_module,
        }
        for item in ordered[:6]
    ] or [
        {
            "title": "Route organized evidence for human review",
            "detail": (
                "No open attention items. A licensed Professional Engineer review "
                "is still required before any final decision."
            ),
            "severity": "info",
            "target_route": ROUTE_WORKFLOW,
            "source_module": "human_review",
        }
    ]
    next_steps = {
        "project_id": project_id,
        "snapshot_id": snapshot.snapshot_id,
        "steps": steps,
        "note": (
            "Recommended review-support steps. None of these approves, certifies, "
            "or finalizes the work."
        ),
    }
    module_links = _module_links_payload(db, project_id)

    _audit(
        db,
        project_id=project_id,
        event_type="command_center_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Project command center viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return {
        "snapshot": snapshot,
        "health_metrics": metrics,
        "attention_items": attention,
        "timeline": timeline,
        "readiness_checks": readiness,
        "next_steps": next_steps,
        "module_links": module_links,
        "reviewer_notes": notes,
        "limitations_note": LIMITATIONS_NOTE,
    }


def _module_links_payload(db: Session, project_id: str) -> dict:
    data = _gather(db, project_id)
    workflow_attention = len(
        [
            i
            for i in data["workflow_items"]
            if i.status in {"needs_follow_up", "needs_more_information"}
        ]
    )

    def link(module, label, route, description, count):
        return {
            "module": module,
            "label": label,
            "route": route,
            "description": description,
            "count": count,
            "severity": _severity_for_count(count) if count else "info",
        }

    links = [
        link("cad_intake", "CAD Intake", ROUTE_CAD_INTAKE, "Upload, parse, and review DXF files and CAD findings.", len(data["cad_files"])),
        link("review_cycles", "Review Cycles", ROUTE_REVIEW_CYCLES, "Resubmittals, revision comparison, and the response cycle.", len(data["resubmittals"])),
        link("workflow_board", "Workflow Board", ROUTE_WORKFLOW, "Track review-support items through triage to handoff.", workflow_attention),
        link("response_package", "Response Package", ROUTE_RESPONSE, "Draft external review response package.", len([i for i in data["response_items"] if i.status == "needs_revision"])),
        link("review_packet", "Review Packet", ROUTE_PACKET, "Assembled review-support packet with evidence traceability.", len(data["packets"])),
        link("plan_sheets", "Plan Sheets", ROUTE_SHEETS, "Plan sheet index with revisions and missing sheet detection.", len(data["plan_sheets"])),
        link("cad_review", "CAD Review", ROUTE_CAD_REVIEW, "CAD-aware metadata, plan references, and consistency findings.", len(data["plan_consistency"])),
        link("sheet_viewer", "Sheet Viewer", ROUTE_SHEET_VIEWER, "Plan sheet viewer with seeded sheet hotspots.", len(data["sheet_hotspots"])),
    ]
    return {
        "project_id": project_id,
        "links": links,
        "note": "The dashboard links into existing modules rather than replacing them.",
    }


def ensure_command_center(db: Session, project_id: str) -> None:
    """Generate an initial command center snapshot once if none exists."""

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.ProjectCommandCenterSnapshot)
        .filter(models.ProjectCommandCenterSnapshot.project_id == project_id)
        .first()
    )
    if existing is None:
        generate_command_center_snapshot(db, project_id)
