"""Seeded submission document records for the Brookside Meadows fixture.

The 19 synthetic document records in the initial submission package, covering
present, partial, missing, referenced, and not-yet-submitted statuses. This is
seeded review-support data, not text extracted from real PDF or CAD files.
"""

from __future__ import annotations

DOCUMENTS = [
    {
        "document_id": "doc_site_narrative",
        "file_name": "site-plan-narrative.pdf",
        "document_type": "site_plan_narrative",
        "status": "present",
        "purpose": "Describe the project and stormwater approach",
        "expected_key_information": "Project scope, phasing intent, BMP strategy",
        "intentionally_missing_or_conflicting_information": (
            "References revised sheet C-3.1 (not included)"
        ),
    },
    {
        "document_id": "doc_existing_conditions",
        "file_name": "existing-conditions-plan.pdf",
        "document_type": "existing_conditions_plan",
        "status": "present",
        "purpose": "Show pre-development site",
        "expected_key_information": (
            "Topography, wood line, meadow, stream, wetland, culvert"
        ),
        "intentionally_missing_or_conflicting_information": None,
    },
    {
        "document_id": "doc_layout_plan",
        "file_name": "layout-plan.pdf",
        "document_type": "layout_plan",
        "status": "present",
        "purpose": "Show lots and roads",
        "expected_key_information": (
            "47 lots, Brookside Drive, loop, Meadow Court cul-de-sac, sidewalks"
        ),
        "intentionally_missing_or_conflicting_information": None,
    },
    {
        "document_id": "doc_grading_drainage",
        "file_name": "grading-and-drainage-plan.pdf",
        "document_type": "grading_drainage_plan",
        "status": "present",
        "purpose": "Show grading and storm system",
        "expected_key_information": "Grading, storm drain, basin locations",
        "intentionally_missing_or_conflicting_information": (
            'Labels basin "Pond A" (conflicts with report\'s "Basin 1")'
        ),
    },
    {
        "document_id": "doc_utility_plan",
        "file_name": "utility-plan.pdf",
        "document_type": "utility_plan",
        "status": "present",
        "purpose": "Show utilities",
        "expected_key_information": (
            "Water main, gravity sewer, pump station, dry utilities"
        ),
        "intentionally_missing_or_conflicting_information": None,
    },
    {
        "document_id": "doc_stormwater_report",
        "file_name": "stormwater-management-report.pdf",
        "document_type": "stormwater_management_report",
        "status": "present",
        "purpose": "Describe permanent stormwater controls",
        "expected_key_information": "BMP selection, treatment train, basin sizing",
        "intentionally_missing_or_conflicting_information": (
            'Uses 25-year design storm; calls basin "Basin 1"; does not address '
            "groundwater separation"
        ),
    },
    {
        "document_id": "doc_hydrology_calcs",
        "file_name": "hydrology-calculations.pdf",
        "document_type": "hydrology_calculations",
        "status": "present",
        "purpose": "Runoff and peak-flow calculations",
        "expected_key_information": "CN, Tc, peak flows existing vs. proposed",
        "intentionally_missing_or_conflicting_information": None,
    },
    {
        "document_id": "doc_hydraulic_calcs",
        "file_name": "hydraulic-calculations.pdf",
        "document_type": "hydraulic_calculations",
        "status": "partial",
        "purpose": "Pipe and outlet sizing",
        "expected_key_information": "Pipe capacity, outlet structure sizing",
        "intentionally_missing_or_conflicting_information": (
            "No downstream culvert capacity analysis"
        ),
    },
    {
        "document_id": "doc_soils_report",
        "file_name": "soils-geotechnical-report.pdf",
        "document_type": "soil_report",
        "status": "present",
        "purpose": "Subsurface conditions",
        "expected_key_information": (
            "Soil groups, borings, seasonal high groundwater"
        ),
        "intentionally_missing_or_conflicting_information": (
            "Notes seasonal high groundwater (separation never reconciled in "
            "stormwater report)"
        ),
    },
    {
        "document_id": "doc_infiltration_logs",
        "file_name": "infiltration-testing-logs.pdf",
        "document_type": "infiltration_testing_documentation",
        "status": "missing",
        "purpose": "Support the infiltration basin",
        "expected_key_information": (
            "Test locations, rates, method, date, depth to groundwater"
        ),
        "intentionally_missing_or_conflicting_information": (
            "Missing or incomplete for a proposed infiltration practice"
        ),
    },
    {
        "document_id": "doc_escp",
        "file_name": "erosion-sediment-control-plan.pdf",
        "document_type": "erosion_control_plan",
        "status": "present",
        "purpose": "Construction-phase controls",
        "expected_key_information": (
            "Silt fence, inlet protection, construction entrance, stabilization"
        ),
        "intentionally_missing_or_conflicting_information": (
            "Not clearly tied to construction phasing"
        ),
    },
    {
        "document_id": "doc_swppp",
        "file_name": "swppp.pdf",
        "document_type": "swppp",
        "status": "present",
        "purpose": "Construction stormwater pollution prevention",
        "expected_key_information": (
            "Controls, inspection commitments, corrective-action procedure"
        ),
        "intentionally_missing_or_conflicting_information": (
            "Template-level; light on site-specific detail"
        ),
    },
    {
        "document_id": "doc_oem_plan",
        "file_name": "operation-maintenance-plan.pdf",
        "document_type": "o_and_m_plan",
        "status": "present",
        "purpose": "Long-term BMP maintenance",
        "expected_key_information": "Tasks, frequency, access, responsible owner",
        "intentionally_missing_or_conflicting_information": (
            'References "HOA maintenance" but HOA responsibility not formally '
            "documented"
        ),
    },
    {
        "document_id": "doc_phasing_plan",
        "file_name": "construction-phasing-plan.pdf",
        "document_type": "construction_phasing_plan",
        "status": "present",
        "purpose": "Construction sequence",
        "expected_key_information": "Two phases: upland then lower meadow",
        "intentionally_missing_or_conflicting_information": (
            "Inconsistent with the erosion and sediment control plan sequencing"
        ),
    },
    {
        "document_id": "doc_inspection_notes",
        "file_name": "inspection-notes.pdf",
        "document_type": "inspection_notes",
        "status": "present",
        "purpose": "Field observations",
        "expected_key_information": "Date, inspector, observations",
        "intentionally_missing_or_conflicting_information": (
            "Flags sediment at basin outlet; no corrective action logged"
        ),
    },
    {
        "document_id": "doc_rfi_log",
        "file_name": "rfi-log.pdf",
        "document_type": "rfi_log",
        "status": "present",
        "purpose": "Track questions",
        "expected_key_information": "RFI number, question, status",
        "intentionally_missing_or_conflicting_information": (
            "RFI asks pipe material; no response recorded"
        ),
    },
    {
        "document_id": "doc_municipal_checklist",
        "file_name": "town-stormwater-checklist.pdf",
        "document_type": "municipal_checklist",
        "status": "present",
        "purpose": "Town submission requirements",
        "expected_key_information": (
            "Required reports, design-storm standard, O&M requirement"
        ),
        "intentionally_missing_or_conflicting_information": (
            "Expects a different design storm than the report's 25-year"
        ),
    },
    {
        "document_id": "doc_comment_response",
        "file_name": "comment-response-letter.pdf",
        "document_type": "comment_response_letter",
        "status": "not_yet_submitted",
        "purpose": "Respond to review comments",
        "expected_key_information": "Responses to each comment",
        "intentionally_missing_or_conflicting_information": (
            "First submission, none yet"
        ),
    },
    {
        "document_id": "doc_revised_c31",
        "file_name": "grading-sheet-C-3.1-REV.pdf",
        "document_type": "grading_drainage_plan",
        "status": "referenced_not_included",
        "purpose": "Revised grading sheet",
        "expected_key_information": "Revised grading per narrative",
        "intentionally_missing_or_conflicting_information": (
            "Referenced but absent from the package"
        ),
    },
]
