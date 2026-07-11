"""Readiness-check builder: derives review readiness checks from the
gathered project data. A ready status means the material is assembled for
human review, not that anything is approved."""

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
