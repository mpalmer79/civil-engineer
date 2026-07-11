"""Timeline builder: derives project timeline events from the gathered
project data for the command center display."""

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
    db_response_packages,
)

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
