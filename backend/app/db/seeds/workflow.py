"""Seeded audit events and evaluation cases for the Brookside Meadows fixture.

The audit events record the seeded review-support workflow trail, and the 8
evaluation cases carry seeded scoring results for the evaluation dashboard.
This is seeded review-support data, not the output of a live review run.
"""

from __future__ import annotations

from app.db.seeds.reference_project import PROJECT_ID, _dt

AUDIT_EVENTS = [
    {
        "audit_event_id": "audit_001",
        "event_type": "project_fixture_loaded",
        "actor_type": "system",
        "related_entity_type": "project",
        "related_entity_id": PROJECT_ID,
        "timestamp": _dt("2026-06-22T13:02:11Z"),
        "description": (
            "Brookside Meadows review fixture loaded with project metadata and "
            "known constraints."
        ),
    },
    {
        "audit_event_id": "audit_002",
        "event_type": "document_package_seeded",
        "actor_type": "system",
        "related_entity_type": "review_package",
        "related_entity_id": "review_package_initial_submission",
        "timestamp": _dt("2026-06-22T13:02:14Z"),
        "description": (
            "Initial submission package registered: 19 document records "
            "(present, partial, missing, referenced, and not-yet-submitted)."
        ),
    },
    {
        "audit_event_id": "audit_003",
        "event_type": "checklist_applied",
        "actor_type": "system",
        "related_entity_type": "checklist",
        "related_entity_id": "stormwater_checklist_v1",
        "timestamp": _dt("2026-06-22T13:02:18Z"),
        "description": (
            "19 stormwater checklist items applied to the project based on "
            "applicability flags (infiltration practice, detention basin, "
            "downstream structure)."
        ),
    },
    {
        "audit_event_id": "audit_004",
        "event_type": "evidence_mapped",
        "actor_type": "system",
        "related_entity_type": "checklist_item",
        "related_entity_id": "chk_infiltration_testing",
        "timestamp": _dt("2026-06-22T13:02:23Z"),
        "description": (
            "Expected evidence for the infiltration-testing item mapped to "
            "supporting document types; no infiltration testing log located in "
            "the package."
        ),
    },
    {
        "audit_event_id": "audit_005",
        "event_type": "finding_generated",
        "actor_type": "system",
        "related_entity_type": "finding",
        "related_entity_id": "find_infiltration_missing",
        "timestamp": _dt("2026-06-22T13:02:25Z"),
        "description": (
            "Review-support finding drafted: infiltration testing not found for "
            "proposed infiltration basin. Status: missing. Routed to human "
            "review."
        ),
    },
    {
        "audit_event_id": "audit_006",
        "event_type": "finding_generated",
        "actor_type": "system",
        "related_entity_type": "finding",
        "related_entity_id": "find_storm_conflict",
        "timestamp": _dt("2026-06-22T13:02:27Z"),
        "description": (
            "Review-support finding drafted: design-storm assumption conflicts "
            "with town standard. Status: conflicting. Routed to human review."
        ),
    },
    {
        "audit_event_id": "audit_007",
        "event_type": "safety_wording_validation",
        "actor_type": "system",
        "related_entity_type": "review_run",
        "related_entity_id": "review_run_001",
        "timestamp": _dt("2026-06-22T13:02:31Z"),
        "description": (
            "Safety wording validation passed for all drafted findings: no "
            "prohibited final-decision language detected."
        ),
    },
    {
        "audit_event_id": "audit_008",
        "event_type": "human_review_action",
        "actor_type": "reviewer",
        "related_entity_type": "finding",
        "related_entity_id": "find_infiltration_missing",
        "timestamp": _dt("2026-06-22T15:41:05Z"),
        "description": (
            "Reviewer (Town Engineer) opened the infiltration-testing finding "
            "and inspected the mapped evidence. Action pending applicant "
            "response."
        ),
    },
    {
        "audit_event_id": "audit_009",
        "event_type": "human_review_action",
        "actor_type": "reviewer",
        "related_entity_type": "finding",
        "related_entity_id": "find_basin_naming",
        "timestamp": _dt("2026-06-22T15:48:52Z"),
        "description": (
            "Reviewer noted the Pond A and Basin 1 naming conflict for inclusion "
            "in the comment letter. Requires reviewer confirmation before "
            "issuance."
        ),
    },
    {
        "audit_event_id": "audit_010",
        "event_type": "evaluation_case_scored",
        "actor_type": "evaluator",
        "related_entity_type": "evaluation_case",
        "related_entity_id": "eval_infiltration_missing",
        "timestamp": _dt("2026-06-22T16:10:00Z"),
        "description": (
            "Evaluation case scored: expected missing-infiltration-testing "
            "finding detected with valid source mapping. Recorded for the "
            "evaluation dashboard."
        ),
    },
]


def _result(
    detected: str,
    citation: float,
    fp: int = 0,
    fn: int = 0,
    unsupported: int = 0,
    prohibited: int = 0,
    human_review: int = 0,
    passed: bool = True,
) -> dict:
    return {
        "expected_findings_detected": detected,
        "source_citation_accuracy": citation,
        "false_positives": fp,
        "false_negatives": fn,
        "unsupported_claims": unsupported,
        "prohibited_wording_count": prohibited,
        "human_review_required": human_review,
        "passed": passed,
    }


EVALUATION_CASES = [
    {
        "eval_case_id": "eval_infiltration_missing",
        "name": "Missing infiltration testing",
        "input_documents": ["doc_stormwater_report", "doc_soils_report"],
        "expected_findings": ["find_infiltration_missing"],
        "expected_risk_level": "high",
        "evaluation_metric": "recall",
        "seeded_result": _result("1 / 1", 0.95, human_review=1),
    },
    {
        "eval_case_id": "eval_storm_conflict",
        "name": "Conflicting storm event assumption",
        "input_documents": [
            "doc_stormwater_report",
            "doc_hydrology_calcs",
            "doc_municipal_checklist",
        ],
        "expected_findings": ["find_storm_conflict"],
        "expected_risk_level": "high",
        "evaluation_metric": "recall",
        "seeded_result": _result("1 / 1", 0.92, human_review=1),
    },
    {
        "eval_case_id": "eval_oem_owner",
        "name": "Missing O&M responsibility",
        "input_documents": ["doc_oem_plan", "doc_site_narrative"],
        "expected_findings": ["find_oem_owner"],
        "expected_risk_level": "high",
        "evaluation_metric": "recall",
        "seeded_result": _result("1 / 1", 0.90, human_review=1),
    },
    {
        "eval_case_id": "eval_rfi_open",
        "name": "Unresolved RFI",
        "input_documents": ["doc_rfi_log"],
        "expected_findings": ["find_rfi_open"],
        "expected_risk_level": "medium",
        "evaluation_metric": "recall",
        "seeded_result": _result("1 / 1", 0.93, human_review=1),
    },
    {
        "eval_case_id": "eval_downstream_capacity",
        "name": "Missing downstream capacity discussion",
        "input_documents": [
            "doc_hydraulic_calcs",
            "doc_stormwater_report",
            "doc_existing_conditions",
        ],
        "expected_findings": ["find_downstream_capacity"],
        "expected_risk_level": "high",
        "evaluation_metric": "recall",
        "seeded_result": _result("1 / 1", 0.88, human_review=1),
    },
    {
        "eval_case_id": "eval_inspection_open",
        "name": "Inspection note without corrective action",
        "input_documents": ["doc_inspection_notes"],
        "expected_findings": ["find_inspection_open"],
        "expected_risk_level": "high",
        "evaluation_metric": "recall",
        "seeded_result": _result("1 / 1", 0.94, human_review=1),
    },
    {
        "eval_case_id": "eval_basin_naming",
        "name": "Conflicting basin names",
        "input_documents": ["doc_grading_drainage", "doc_stormwater_report"],
        "expected_findings": ["find_basin_naming"],
        "expected_risk_level": "medium",
        "evaluation_metric": "source_citation_accuracy",
        "seeded_result": _result("1 / 1", 0.97, human_review=1),
    },
    {
        "eval_case_id": "eval_clean_control",
        "name": "Clean control, no false positives",
        "input_documents": [
            "doc_existing_conditions",
            "doc_layout_plan",
            "doc_hydrology_calcs",
        ],
        "expected_findings": [],
        "expected_risk_level": "low",
        "evaluation_metric": "no_false_positive",
        "seeded_result": _result("0 / 0", 1.0, human_review=0),
    },
]
