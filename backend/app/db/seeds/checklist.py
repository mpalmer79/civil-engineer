"""Seeded stormwater checklist items for the Brookside Meadows fixture.

The 19 checklist items applied to the project, each with an expected
review-support status and links to the planted review issues. This is seeded
review-support data; no item records a final engineering decision.
"""

from __future__ import annotations


def _docs(csv: str) -> list[str]:
    """Split a comma separated supporting-documents string into a list."""

    return [item.strip() for item in csv.split(",") if item.strip()]


CHECKLIST = [
    {
        "checklist_item_id": "chk_pkg_completeness",
        "category": "Completeness",
        "requirement": "Package includes a stormwater or drainage report",
        "expected_evidence": "Stormwater or drainage report present",
        "supporting_documents": _docs("stormwater_management_report"),
        "risk_level": "high",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "supported",
        "planted_issue": None,
    },
    {
        "checklist_item_id": "chk_design_storm_stated",
        "category": "Design storm",
        "requirement": "Design-storm assumptions are stated",
        "expected_evidence": "Storm event, recurrence, rainfall depth",
        "supporting_documents": _docs(
            "stormwater_management_report, hydrology_calculations"
        ),
        "risk_level": "high",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "supported",
        "planted_issue": None,
    },
    {
        "checklist_item_id": "chk_design_storm_consistent",
        "category": "Design storm",
        "requirement": (
            "Design storm matches the municipal standard and is consistent "
            "across documents"
        ),
        "expected_evidence": "Same event in report, calcs, and town checklist",
        "supporting_documents": _docs(
            "stormwater_management_report, hydrology_calculations, "
            "municipal_checklist"
        ),
        "risk_level": "high",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "conflicting",
        "planted_issue": "I-1",
    },
    {
        "checklist_item_id": "chk_drainage_areas",
        "category": "Drainage areas",
        "requirement": "Existing and proposed drainage areas identified",
        "expected_evidence": "Drainage area maps or tables",
        "supporting_documents": _docs(
            "existing_conditions_plan, grading_drainage_plan, "
            "hydrology_calculations"
        ),
        "risk_level": "medium",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "supported",
        "planted_issue": None,
    },
    {
        "checklist_item_id": "chk_runoff_calcs",
        "category": "Runoff",
        "requirement": "Runoff calcs for existing and proposed conditions",
        "expected_evidence": "Peak flow or volume calcs",
        "supporting_documents": _docs("hydrology_calculations"),
        "risk_level": "high",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "supported",
        "planted_issue": None,
    },
    {
        "checklist_item_id": "chk_bmp_identified",
        "category": "BMP",
        "requirement": "Proposed stormwater BMPs are identified",
        "expected_evidence": "BMP type, location, purpose",
        "supporting_documents": _docs(
            "stormwater_management_report, grading_drainage_plan"
        ),
        "risk_level": "medium",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "supported",
        "planted_issue": None,
    },
    {
        "checklist_item_id": "chk_infiltration_testing",
        "category": "Infiltration",
        "requirement": (
            "If infiltration is proposed, infiltration testing is included"
        ),
        "expected_evidence": "Test locations, rates, method, date",
        "supporting_documents": _docs(
            "soil_report, infiltration_testing_documentation"
        ),
        "risk_level": "high",
        "applies_when": "has_infiltration_practice",
        "expected_status_for_brookside_meadows": "missing",
        "planted_issue": "I-2",
    },
    {
        "checklist_item_id": "chk_groundwater_separation",
        "category": "Infiltration",
        "requirement": (
            "Separation to seasonal high groundwater is addressed for "
            "infiltration or bioretention"
        ),
        "expected_evidence": "Groundwater depth and separation discussion",
        "supporting_documents": _docs(
            "soil_report, stormwater_management_report"
        ),
        "risk_level": "high",
        "applies_when": "has_infiltration_practice",
        "expected_status_for_brookside_meadows": "unclear",
        "planted_issue": "I-3",
    },
    {
        "checklist_item_id": "chk_soil_groundwater_doc",
        "category": "Soils",
        "requirement": "Soil and groundwater conditions are documented",
        "expected_evidence": "Borings, soil groups, seasonal high groundwater",
        "supporting_documents": _docs("soil_report"),
        "risk_level": "high",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "supported",
        "planted_issue": None,
    },
    {
        "checklist_item_id": "chk_outfall_identified",
        "category": "Outfall",
        "requirement": "Outfalls or discharge points identified",
        "expected_evidence": "Outfall labels, receiving water, path",
        "supporting_documents": _docs(
            "grading_drainage_plan, stormwater_management_report"
        ),
        "risk_level": "medium",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "supported",
        "planted_issue": None,
    },
    {
        "checklist_item_id": "chk_downstream_capacity",
        "category": "Downstream",
        "requirement": (
            "Downstream conveyance capacity is discussed where a downstream "
            "structure exists"
        ),
        "expected_evidence": "Downstream culvert capacity analysis",
        "supporting_documents": _docs(
            "hydraulic_calculations, stormwater_management_report"
        ),
        "risk_level": "high",
        "applies_when": "has_downstream_structure",
        "expected_status_for_brookside_meadows": "missing",
        "planted_issue": "I-4",
    },
    {
        "checklist_item_id": "chk_erosion_controls",
        "category": "Erosion",
        "requirement": "Erosion and sediment controls are shown",
        "expected_evidence": (
            "Silt fence, inlet protection, construction entrance, stabilization"
        ),
        "supporting_documents": _docs("erosion_control_plan, swppp"),
        "risk_level": "medium",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "supported",
        "planted_issue": None,
    },
    {
        "checklist_item_id": "chk_escp_phasing",
        "category": "Erosion",
        "requirement": "Erosion and sediment controls are tied to phasing",
        "expected_evidence": "Phased control sequencing",
        "supporting_documents": _docs(
            "erosion_control_plan, construction_phasing_plan"
        ),
        "risk_level": "medium",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "conflicting",
        "planted_issue": "I-6",
    },
    {
        "checklist_item_id": "chk_oem_plan",
        "category": "O&M",
        "requirement": "Long-term operation and maintenance is addressed",
        "expected_evidence": "Tasks, schedule, access",
        "supporting_documents": _docs("o_and_m_plan"),
        "risk_level": "high",
        "applies_when": "has_detention_basin OR has_infiltration_practice",
        "expected_status_for_brookside_meadows": "supported",
        "planted_issue": None,
    },
    {
        "checklist_item_id": "chk_oem_owner",
        "category": "O&M",
        "requirement": "Responsible maintenance party is clearly identified",
        "expected_evidence": (
            "Named owner (HOA, municipality, or private) with binding "
            "responsibility"
        ),
        "supporting_documents": _docs("o_and_m_plan, site_plan_narrative"),
        "risk_level": "high",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "unclear",
        "planted_issue": "I-5",
    },
    {
        "checklist_item_id": "chk_rfi_closure",
        "category": "RFI",
        "requirement": "RFIs are resolved or clearly tracked",
        "expected_evidence": "RFI status and response",
        "supporting_documents": _docs("rfi_log"),
        "risk_level": "medium",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "conflicting",
        "planted_issue": "I-8",
    },
    {
        "checklist_item_id": "chk_inspection_closeout",
        "category": "Inspection",
        "requirement": (
            "Inspection deficiencies have corrective-action closeout"
        ),
        "expected_evidence": "Corrective action status",
        "supporting_documents": _docs("inspection_notes"),
        "risk_level": "high",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "unresolved",
        "planted_issue": "I-7",
    },
    {
        "checklist_item_id": "chk_reference_consistency",
        "category": "Consistency",
        "requirement": (
            "Basin, sheet, and structure references are consistent across "
            "documents"
        ),
        "expected_evidence": "Matching labels across plan and report",
        "supporting_documents": _docs(
            "grading_drainage_plan, stormwater_management_report"
        ),
        "risk_level": "medium",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "conflicting",
        "planted_issue": "I-9",
    },
    {
        "checklist_item_id": "chk_referenced_sheets_present",
        "category": "Completeness",
        "requirement": "Referenced revised sheets are included in the package",
        "expected_evidence": "All cited sheets present",
        "supporting_documents": _docs(
            "site_plan_narrative, grading_drainage_plan"
        ),
        "risk_level": "medium",
        "applies_when": "always",
        "expected_status_for_brookside_meadows": "missing",
        "planted_issue": "I-10",
    },
]
