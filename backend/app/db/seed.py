"""Seed loading for the Brookside Meadows review fixture.

This module is the canonical runtime data source for the Phase 2 backend. The
values mirror the Phase 1 TypeScript seed data under the repository data folder.
Brookside Meadows is a fictional project used for a portfolio demonstration. All
people, firms, documents, and values are synthetic, and the package contains
intentional gaps and conflicts so the review-support system has concrete work to
surface.

Do not change the core fixture facts: 38.5 acres, 47 lots, 22 disturbed acres,
19 documents, 19 checklist items, 10 planted review issues, 8 evaluation cases.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.db import models
from app.db.database import SessionLocal, init_db

PROJECT_ID = "proj_brookside_meadows"


def _dt(value: str) -> datetime:
    """Parse an ISO 8601 timestamp, accepting a trailing Z for UTC."""

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


PROJECT = {
    "project_id": PROJECT_ID,
    "project_name": "Brookside Meadows Residential Subdivision",
    "project_type": "Residential subdivision",
    "location_context": (
        "Suburban-to-rural fringe parcel on the edge of an established "
        "neighborhood"
    ),
    "jurisdiction": "Town of Hartwell",
    "review_type": (
        "Subdivision and site plan with post-construction stormwater review"
    ),
    "review_domain": "stormwater",
    "acreage": 38.5,
    "disturbed_area": 22.0,
    "proposed_lots": 47,
    "status": "ready_for_review",
    "summary": (
        "A regional homebuilder has proposed Brookside Meadows: a 47-lot "
        "single-family subdivision on a 38.5-acre former farm parcel at the "
        "edge of an established neighborhood in the Town of Hartwell. The site "
        "falls from a wooded upland in the northwest toward an intermittent "
        "stream and a wetland buffer along the southeast property line, where "
        "runoff currently sheet-flows to an existing culvert under Quarry Road. "
        "The applicant proposes a mix of green infrastructure (bioretention and "
        "an infiltration basin) and conventional gray infrastructure (a wet "
        "detention basin and a piped storm drain network). The Town Engineer "
        "must review the package for completeness and technical adequacy before "
        "the Planning Board acts."
    ),
    "site_conditions": [
        {
            "type": "soils",
            "label": "Mixed soil conditions",
            "description": (
                "Hydrologic soil groups B and C with a band of slower-draining "
                "C/D soils and a possible restrictive layer in the lower "
                "meadow. Infiltration feasibility varies sharply across the "
                "site."
            ),
        },
        {
            "type": "groundwater",
            "label": "Seasonal high groundwater",
            "description": (
                "Soils report notes seasonal high groundwater within about 2.5 "
                "to 3.5 ft of existing grade in the low southeastern portion of "
                "the site, directly relevant to infiltration and bioretention "
                "separation."
            ),
        },
        {
            "type": "wetland_buffer",
            "label": "Wetland buffer",
            "description": (
                "A delineated wetland fringes Brook Run along the southeast "
                "boundary. The town applies a 100-ft buffer near several "
                "proposed grading and outfall features."
            ),
        },
        {
            "type": "stream",
            "label": "Brook Run stream corridor",
            "description": (
                "An intermittent stream crosses the southeast corner and "
                "conveys site runoff toward the Quarry Road culvert. Existing "
                "condition is predominantly sheet flow and shallow concentrated "
                "flow."
            ),
        },
        {
            "type": "slope",
            "label": "Sloping terrain",
            "description": (
                "The site grades from about 412 ft in the northwest to about "
                "358 ft near the southeast corner, roughly 54 ft of fall, with "
                "steeper 8 to 15 percent slopes on the western wood line."
            ),
        },
        {
            "type": "downstream_structure",
            "label": "Quarry Road culvert",
            "description": (
                "Runoff leaves the site through an existing 36-inch reinforced "
                "concrete culvert under Quarry Road. Neighbors downstream have "
                "reported road-edge ponding in large storms."
            ),
        },
        {
            "type": "adjacent_use",
            "label": "Adjacent neighborhood",
            "description": (
                "An established neighborhood (Quarry Road Estates) abuts the "
                "south and east property lines. Abutters are sensitive to "
                "drainage changes, construction traffic, and tree clearing."
            ),
        },
    ],
    "proposed_improvements": [
        {
            "type": "detention_basin",
            "label": "Basin 1",
            "aliases": ["Pond A"],
            "description": (
                "Wet detention basin in the southeast low area providing "
                "peak-flow attenuation before the Quarry Road culvert outfall."
            ),
        },
        {
            "type": "infiltration_basin",
            "label": "Basin 2",
            "aliases": [],
            "description": (
                "Infiltration basin proposed in the meadow to reduce runoff "
                "volume and provide groundwater recharge. Feasibility hinges on "
                "infiltration testing and groundwater separation."
            ),
        },
        {
            "type": "bioretention",
            "label": "Bioretention Cells BR-1 / BR-2",
            "aliases": [],
            "description": (
                "Two roadside bioretention cells along Brookside Drive for "
                "water-quality treatment of road runoff."
            ),
        },
        {
            "type": "storm_drain",
            "label": "Storm Drain Network",
            "aliases": [],
            "description": (
                "Curb inlets, catch basins, and reinforced concrete or HDPE "
                "storm drain pipe conveying road runoff toward the management "
                "facilities."
            ),
        },
        {
            "type": "riprap_apron",
            "label": "Outlet Protection",
            "aliases": [],
            "description": (
                "Riprap aprons at the detention basin outlet and at the culvert "
                "headwall to control scour."
            ),
        },
    ],
    "known_constraints": [
        "Infiltration feasibility versus shallow seasonal high groundwater",
        "Downstream culvert capacity and reported road-edge ponding",
        "Wetland buffer encroachment near proposed outfalls and grading",
        "Phased clearing of about 22 acres on slopes draining to a stream",
        "Long-term maintenance ownership of shared green and gray facilities",
    ],
}


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


HOTSPOTS = [
    {
        "hotspot_id": "hotspot_wet_detention_basin",
        "name": "Wet detention basin (Basin 1)",
        "category": "stormwater",
        "short_description": (
            "Gray-infrastructure detention basin attenuating peak flow before "
            "the culvert outfall."
        ),
        "civil_purpose": (
            "Peak-flow attenuation and water-quality settling prior to "
            "discharge toward the Quarry Road culvert."
        ),
        "related_checklist_items": [
            "chk_bmp_identified",
            "chk_outfall_identified",
            "chk_reference_consistency",
        ],
        "related_planted_issues": ["I-9"],
        "future_drilldown": (
            "Drill-down to basin sizing evidence, outfall details, and the Pond "
            "A and Basin 1 naming-conflict finding."
        ),
        "position_x_percent": 68.0,
        "position_y_percent": 72.0,
    },
    {
        "hotspot_id": "hotspot_infiltration_meadow_basin",
        "name": "Infiltration basin (Basin 2)",
        "category": "stormwater",
        "short_description": (
            "Green-infrastructure infiltration basin in the meadow for volume "
            "reduction and recharge."
        ),
        "civil_purpose": (
            "Runoff volume reduction and groundwater recharge. Feasibility "
            "depends on infiltration testing and groundwater separation."
        ),
        "related_checklist_items": [
            "chk_infiltration_testing",
            "chk_groundwater_separation",
            "chk_soil_groundwater_doc",
        ],
        "related_planted_issues": ["I-2", "I-3"],
        "future_drilldown": (
            "Drill-down to infiltration testing evidence (missing) and the "
            "seasonal high groundwater separation discussion."
        ),
        "position_x_percent": 52.0,
        "position_y_percent": 60.0,
    },
    {
        "hotspot_id": "hotspot_wetland_stream_corridor",
        "name": "Wetland buffer and Brook Run corridor",
        "category": "wetland",
        "short_description": (
            "Delineated wetland and intermittent stream with a 100-ft town "
            "buffer along the southeast boundary."
        ),
        "civil_purpose": (
            "Protected resource area; proposed outfalls and grading near the "
            "buffer require Conservation Commission coordination."
        ),
        "related_checklist_items": [
            "chk_outfall_identified",
            "chk_downstream_capacity",
        ],
        "related_planted_issues": [],
        "future_drilldown": (
            "Drill-down to buffer encroachment review, outfall locations, and "
            "receiving-water context."
        ),
        "position_x_percent": 80.0,
        "position_y_percent": 85.0,
    },
    {
        "hotspot_id": "hotspot_quarry_road_culvert",
        "name": "Quarry Road culvert",
        "category": "stormwater",
        "short_description": (
            "Existing 36-inch culvert and downstream discharge point with "
            "reported road-edge ponding."
        ),
        "civil_purpose": (
            "Downstream conveyance structure; post-development flows must not "
            "worsen downstream conditions."
        ),
        "related_checklist_items": ["chk_downstream_capacity"],
        "related_planted_issues": ["I-4"],
        "future_drilldown": (
            "Drill-down to the downstream capacity analysis (missing) and the "
            "downstream ponding concern."
        ),
        "position_x_percent": 90.0,
        "position_y_percent": 78.0,
    },
    {
        "hotspot_id": "hotspot_construction_entrance",
        "name": "Construction entrance",
        "category": "erosion_control",
        "short_description": (
            "Stabilized construction entrance off Quarry Road to control "
            "tracked sediment."
        ),
        "civil_purpose": (
            "Construction-phase access point and sediment-tracking control at "
            "the site entrance."
        ),
        "related_checklist_items": ["chk_erosion_controls", "chk_escp_phasing"],
        "related_planted_issues": [],
        "future_drilldown": (
            "Drill-down to the erosion and sediment control plan and "
            "construction sequencing."
        ),
        "position_x_percent": 84.0,
        "position_y_percent": 64.0,
    },
    {
        "hotspot_id": "hotspot_erosion_control_perimeter",
        "name": "Erosion control perimeter",
        "category": "erosion_control",
        "short_description": (
            "Silt fence and perimeter controls along the downhill limits of "
            "disturbance near the buffer."
        ),
        "civil_purpose": (
            "Perimeter sediment control during phased clearing on slopes "
            "draining toward Brook Run."
        ),
        "related_checklist_items": ["chk_erosion_controls", "chk_escp_phasing"],
        "related_planted_issues": ["I-6"],
        "future_drilldown": (
            "Drill-down to the erosion and sediment control phasing finding and "
            "stabilization timing."
        ),
        "position_x_percent": 40.0,
        "position_y_percent": 78.0,
    },
    {
        "hotspot_id": "hotspot_loop_road_lots",
        "name": "Loop road subdivision lots",
        "category": "lots",
        "short_description": (
            "Upland lots served by the loop road, with rooftop and driveway "
            "impervious cover."
        ),
        "civil_purpose": (
            "Primary residential development area contributing new impervious "
            "runoff to the storm drain network."
        ),
        "related_checklist_items": ["chk_drainage_areas", "chk_runoff_calcs"],
        "related_planted_issues": [],
        "future_drilldown": (
            "Drill-down to drainage-area mapping and runoff calculations for "
            "proposed conditions."
        ),
        "position_x_percent": 35.0,
        "position_y_percent": 38.0,
    },
    {
        "hotspot_id": "hotspot_culdesac_lower_lots",
        "name": "Cul-de-sac lower lots",
        "category": "lots",
        "short_description": (
            "Lower lots on Meadow Court near the buffer and shallow groundwater "
            "area."
        ),
        "civil_purpose": (
            "Lower-elevation lots sensitive to groundwater and proximity to the "
            "wetland buffer."
        ),
        "related_checklist_items": [
            "chk_groundwater_separation",
            "chk_drainage_areas",
        ],
        "related_planted_issues": ["I-3"],
        "future_drilldown": (
            "Drill-down to groundwater separation context and lower-lot grading."
        ),
        "position_x_percent": 62.0,
        "position_y_percent": 50.0,
    },
    {
        "hotspot_id": "hotspot_utility_pump_station",
        "name": "Utility and pump station area",
        "category": "utility",
        "short_description": (
            "Water main, gravity sewer, and a sanitary pump station serving the "
            "low lots."
        ),
        "civil_purpose": (
            "Utility extensions and pump station; storm-drain and buffer "
            "crossings are future coordination points."
        ),
        "related_checklist_items": ["chk_rfi_closure"],
        "related_planted_issues": ["I-8"],
        "future_drilldown": (
            "Drill-down to the open pipe-material RFI and utility and storm "
            "crossing coordination."
        ),
        "position_x_percent": 58.0,
        "position_y_percent": 30.0,
    },
    {
        "hotspot_id": "hotspot_planted_review_issues",
        "name": "Planted review issue locations",
        "category": "risk",
        "short_description": (
            "Overlay summarizing where the ten planted review issues surface "
            "across the package."
        ),
        "civil_purpose": (
            "Demonstration overlay linking map locations to the expected "
            "review-support findings."
        ),
        "related_checklist_items": [
            "chk_design_storm_consistent",
            "chk_infiltration_testing",
            "chk_downstream_capacity",
            "chk_oem_owner",
            "chk_inspection_closeout",
            "chk_referenced_sheets_present",
        ],
        "related_planted_issues": [
            "I-1",
            "I-2",
            "I-3",
            "I-4",
            "I-5",
            "I-6",
            "I-7",
            "I-8",
            "I-9",
            "I-10",
        ],
        "future_drilldown": (
            "Drill-down to the full findings list with map-linked evidence and "
            "human review status."
        ),
        "position_x_percent": 22.0,
        "position_y_percent": 60.0,
    },
]


def seed_is_loaded(db: Session) -> bool:
    """Return True if the Brookside Meadows project is already present."""

    return db.get(models.Project, PROJECT_ID) is not None


def seed_database(db: Session, *, force: bool = False) -> None:
    """Load the Brookside Meadows fixture into the database.

    If the project already exists and force is False, seeding is skipped so the
    operation is idempotent. With force=True, existing fixture rows are removed
    first and reloaded.
    """

    if seed_is_loaded(db):
        if not force:
            return
        for model in (
            models.Hotspot,
            models.EvaluationCase,
            models.AuditEvent,
            models.Finding,
            models.ChecklistItem,
            models.Document,
            models.Project,
        ):
            db.query(model).delete()
        db.commit()

    db.add(models.Project(**PROJECT))
    db.add_all(
        models.Document(project_id=PROJECT_ID, **doc) for doc in DOCUMENTS
    )
    db.add_all(
        models.ChecklistItem(
            project_id=PROJECT_ID, review_domain="stormwater", **item
        )
        for item in CHECKLIST
    )
    db.add_all(
        models.Finding(project_id=PROJECT_ID, **finding) for finding in FINDINGS
    )
    db.add_all(
        models.AuditEvent(project_id=PROJECT_ID, **event) for event in AUDIT_EVENTS
    )
    db.add_all(
        models.EvaluationCase(project_id=PROJECT_ID, **case)
        for case in EVALUATION_CASES
    )
    db.add_all(
        models.Hotspot(project_id=PROJECT_ID, **spot) for spot in HOTSPOTS
    )
    db.commit()


def main() -> None:
    """Create tables and load the seed data. Used by python -m app.db.seed."""

    init_db()
    db = SessionLocal()
    try:
        seed_database(db, force=True)
        print(
            "Seeded Brookside Meadows: "
            f"{len(DOCUMENTS)} documents, {len(CHECKLIST)} checklist items, "
            f"{len(FINDINGS)} findings, {len(AUDIT_EVENTS)} audit events, "
            f"{len(EVALUATION_CASES)} evaluation cases, {len(HOTSPOTS)} hotspots."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
