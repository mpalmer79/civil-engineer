"""Health-metric builder: derives command center metrics from the gathered
project data. Descriptive counts, never engineering conclusions."""

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
