"""Shared derivations over the gathered command center data dict."""

from __future__ import annotations


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


def db_response_packages(data: dict) -> list:
    # Helper kept separate so the timeline reads response packages from the
    # gather set without an extra query path.
    return data.get("response_packages", [])
