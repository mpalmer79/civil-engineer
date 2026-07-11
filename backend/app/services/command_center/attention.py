"""Attention-item builder: derives reviewer attention items from the
gathered project data. Review-support records only; every item needs a
human decision."""

from __future__ import annotations

from app.db import models
from app.services.command_center.shared import (
    ROUTE_CAD_INTAKE,
    ROUTE_CAD_REVIEW,
    ROUTE_CHECKLIST,
    ROUTE_DOCUMENTS,
    ROUTE_PACKET,
    ROUTE_RESPONSE,
    ROUTE_REVIEW_CYCLES,
    ROUTE_SHEETS,
    ROUTE_SHEET_VIEWER,
    ROUTE_WORKFLOW,
    _now,
    _short,
)

from app.services.command_center.derivations import (
    _comparisons_needing_review,
    _evidence_gap_items,
    _low_confidence_mappings,
    _open_carry_forwards,
    _open_follow_ups,
    _resubmittals_needing_comparison,
    _unmapped_responses,
    _unpromoted_findings,
)

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
