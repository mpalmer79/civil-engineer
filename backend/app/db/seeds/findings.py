"""Seeded review-support findings for the Brookside Meadows fixture.

The 10 planted review-support findings, one for each intentional gap or
conflict in the package. Every finding is routed to human review; none is a
final engineering decision.
"""

from __future__ import annotations

FINDINGS = [
    {
        "finding_id": "find_storm_conflict",
        "planted_issue": "I-1",
        "title": "Design-storm assumption conflicts with town standard",
        "category": "Design storm",
        "risk_level": "high",
        "expected_status": "conflicting",
        "evidence_to_find": (
            "Report states a 25-year storm; the town checklist expects a "
            "different event"
        ),
        "reason_it_matters": (
            "Inconsistent design-storm criteria can invalidate review "
            "conclusions about peak flow and basin sizing."
        ),
        "recommended_human_action": (
            "Confirm the applicable town standard and request a correction or "
            "clarification from the applicant."
        ),
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_design_storm_consistent"],
        "related_documents": [
            "doc_stormwater_report",
            "doc_municipal_checklist",
            "doc_hydrology_calcs",
        ],
    },
    {
        "finding_id": "find_infiltration_missing",
        "planted_issue": "I-2",
        "title": "Infiltration testing not found for proposed infiltration basin",
        "category": "Infiltration",
        "risk_level": "high",
        "expected_status": "missing",
        "evidence_to_find": (
            "An infiltration basin is proposed, but no field infiltration "
            "testing logs are in the package"
        ),
        "reason_it_matters": (
            "Infiltration BMPs depend on site-specific testing; without it, "
            "feasibility and sizing cannot be confirmed."
        ),
        "recommended_human_action": (
            "Request field infiltration testing documentation or a design "
            "revision."
        ),
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_infiltration_testing"],
        "related_documents": [
            "doc_stormwater_report",
            "doc_soils_report",
            "doc_infiltration_logs",
        ],
    },
    {
        "finding_id": "find_gw_separation",
        "planted_issue": "I-3",
        "title": "Groundwater separation for infiltration not addressed",
        "category": "Infiltration",
        "risk_level": "high",
        "expected_status": "unclear",
        "evidence_to_find": (
            "Soils report notes seasonal high groundwater; the stormwater "
            "report omits a separation discussion"
        ),
        "reason_it_matters": (
            "Inadequate separation to seasonal high groundwater undermines "
            "infiltration feasibility and performance."
        ),
        "recommended_human_action": (
            "Request a separation analysis that references the documented "
            "seasonal high groundwater depth."
        ),
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_groundwater_separation"],
        "related_documents": ["doc_soils_report", "doc_stormwater_report"],
    },
    {
        "finding_id": "find_downstream_capacity",
        "planted_issue": "I-4",
        "title": "Downstream culvert capacity not analyzed",
        "category": "Downstream",
        "risk_level": "high",
        "expected_status": "missing",
        "evidence_to_find": (
            "The Quarry Road culvert is referenced, but no downstream capacity "
            "analysis is included"
        ),
        "reason_it_matters": (
            "Post-development peak flows could worsen reported downstream "
            "road-edge ponding if capacity is not evaluated."
        ),
        "recommended_human_action": (
            "Request a downstream conveyance or culvert capacity analysis."
        ),
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_downstream_capacity"],
        "related_documents": [
            "doc_hydraulic_calcs",
            "doc_stormwater_report",
            "doc_existing_conditions",
        ],
    },
    {
        "finding_id": "find_oem_owner",
        "planted_issue": "I-5",
        "title": "Maintenance owner not clearly bound",
        "category": "O&M",
        "risk_level": "high",
        "expected_status": "unclear",
        "evidence_to_find": (
            'The O&M plan cites "HOA maintenance" without documented, binding '
            "responsibility"
        ),
        "reason_it_matters": (
            "Unclear long-term maintenance responsibility creates a failure "
            "risk for shared stormwater facilities."
        ),
        "recommended_human_action": (
            "Request formal documentation of HOA maintenance responsibility and "
            "access."
        ),
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_oem_owner"],
        "related_documents": ["doc_oem_plan", "doc_site_narrative"],
    },
    {
        "finding_id": "find_escp_phasing",
        "planted_issue": "I-6",
        "title": "Erosion control sequencing not tied to phasing",
        "category": "Erosion",
        "risk_level": "medium",
        "expected_status": "conflicting",
        "evidence_to_find": (
            "The erosion and sediment control plan lacks phased sequencing "
            "consistent with the phasing plan"
        ),
        "reason_it_matters": (
            "Phased clearing on slopes draining to a stream raises "
            "sediment-control sequencing risk."
        ),
        "recommended_human_action": (
            "Request phased erosion and sediment control sequencing aligned with "
            "the construction phasing plan."
        ),
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_escp_phasing"],
        "related_documents": ["doc_escp", "doc_phasing_plan"],
    },
    {
        "finding_id": "find_inspection_open",
        "planted_issue": "I-7",
        "title": "Inspection deficiency without corrective action",
        "category": "Inspection",
        "risk_level": "high",
        "expected_status": "unresolved",
        "evidence_to_find": (
            "An inspection note flags sediment at the basin outlet, but no "
            "corrective action is logged"
        ),
        "reason_it_matters": (
            "A field deficiency with no recorded closeout may remain unresolved."
        ),
        "recommended_human_action": (
            "Request corrective-action evidence or closeout documentation."
        ),
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_inspection_closeout"],
        "related_documents": ["doc_inspection_notes"],
    },
    {
        "finding_id": "find_rfi_open",
        "planted_issue": "I-8",
        "title": "Open RFI on pipe material with no response",
        "category": "RFI",
        "risk_level": "medium",
        "expected_status": "conflicting",
        "evidence_to_find": (
            "An RFI asks about pipe material, but no response is recorded in the "
            "log"
        ),
        "reason_it_matters": (
            "An open RFI can signal an unresolved design detail that affects the "
            "storm drain network."
        ),
        "recommended_human_action": (
            "Hold the related item pending a response; confirm the proposed pipe "
            "material."
        ),
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_rfi_closure"],
        "related_documents": ["doc_rfi_log"],
    },
    {
        "finding_id": "find_basin_naming",
        "planted_issue": "I-9",
        "title": "Inconsistent basin naming across documents",
        "category": "Consistency",
        "risk_level": "medium",
        "expected_status": "conflicting",
        "evidence_to_find": (
            'The grading plan labels the basin "Pond A" while the stormwater '
            'report calls it "Basin 1"'
        ),
        "reason_it_matters": (
            "Conflicting labels across documents create review confusion and "
            "traceability gaps."
        ),
        "recommended_human_action": (
            "Request consistent basin naming across the plan set and report."
        ),
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_reference_consistency"],
        "related_documents": ["doc_grading_drainage", "doc_stormwater_report"],
    },
    {
        "finding_id": "find_missing_sheet",
        "planted_issue": "I-10",
        "title": "Referenced revised grading sheet C-3.1 not included",
        "category": "Completeness",
        "risk_level": "medium",
        "expected_status": "missing",
        "evidence_to_find": (
            "The narrative cites a revised sheet C-3.1 that is absent from the "
            "package"
        ),
        "reason_it_matters": (
            "A cited revision that is missing cannot be reviewed and may hide "
            "material changes."
        ),
        "recommended_human_action": "Request the missing revised grading sheet C-3.1.",
        "human_review_status": "requires_human_review",
        "related_checklist_items": ["chk_referenced_sheets_present"],
        "related_documents": ["doc_site_narrative", "doc_revised_c31"],
    },
]
