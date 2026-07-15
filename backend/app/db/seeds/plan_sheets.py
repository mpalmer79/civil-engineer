"""Seed loading for the Phase 6 Brookside Meadows plan sheet and CAD data.

This module seeds the plan sheet index, CAD-aware feature metadata, and plan
references for the Brookside Meadows fixture, then generates the plan
consistency findings by running the consistency service against the seeded
references and sheets.

All data is synthetic. No real plan sheets, client files, or CAD drawings are
used. The CAD-aware metadata is seeded, not extracted from DWG or DXF files, and
nothing here verifies a drawing as correct or a design as sound.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import SessionLocal, init_db
from app.db.seeds.reference_project import PROJECT_ID


# Plan sheet index. Sheet C-3.1 is intentionally referenced but not included so
# the missing sheet detection has concrete work to surface.
PLAN_SHEETS = [
    {
        "sheet_id": "sheet_c00",
        "sheet_number": "C-0.0",
        "sheet_title": "Cover Sheet",
        "discipline": "cover",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "present",
        "file_name": "C-0.0-cover-sheet.pdf",
        "sheet_purpose": "Sheet index, project location, and drawing list.",
        "related_documents": ["doc_site_narrative"],
        "related_checklist_items": [],
        "related_findings": [],
    },
    {
        "sheet_id": "sheet_c10",
        "sheet_number": "C-1.0",
        "sheet_title": "Existing Conditions Plan",
        "discipline": "existing_conditions",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "present",
        "file_name": "C-1.0-existing-conditions.pdf",
        "sheet_purpose": (
            "Pre-development topography, wood line, meadow, stream, wetland, and "
            "the Quarry Road culvert."
        ),
        "related_documents": ["doc_existing_conditions"],
        "related_checklist_items": ["chk_drainage_areas"],
        "related_findings": [],
    },
    {
        "sheet_id": "sheet_c20",
        "sheet_number": "C-2.0",
        "sheet_title": "Subdivision Layout Plan",
        "discipline": "layout",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "present",
        "file_name": "C-2.0-layout-plan.pdf",
        "sheet_purpose": (
            "Lot layout, Brookside Drive, the loop road, and the Meadow Court "
            "cul-de-sac."
        ),
        "related_documents": ["doc_layout_plan"],
        "related_checklist_items": ["chk_drainage_areas"],
        "related_findings": [],
    },
    {
        "sheet_id": "sheet_c30",
        "sheet_number": "C-3.0",
        "sheet_title": "Grading and Drainage Plan",
        "discipline": "grading",
        "revision": "1",
        "revision_date": "2026-04-30",
        "status": "present",
        "file_name": "C-3.0-grading-drainage.pdf",
        "sheet_purpose": (
            "Proposed grading, the storm drain network, and basin locations."
        ),
        "related_documents": ["doc_grading_drainage", "doc_stormwater_report"],
        "related_checklist_items": [
            "chk_reference_consistency",
            "chk_bmp_identified",
        ],
        "related_findings": ["find_basin_naming"],
    },
    {
        "sheet_id": "sheet_c31",
        "sheet_number": "C-3.1",
        "sheet_title": "Revised Grading and Drainage Plan",
        "discipline": "grading",
        "revision": "2",
        "revision_date": None,
        "status": "referenced_not_included",
        "file_name": "C-3.1-grading-drainage-REV.pdf",
        "sheet_purpose": (
            "Revised grading sheet cited in the narrative but absent from the "
            "submitted package."
        ),
        "related_documents": ["doc_site_narrative", "doc_revised_c31"],
        "related_checklist_items": ["chk_referenced_sheets_present"],
        "related_findings": ["find_missing_sheet"],
    },
    {
        "sheet_id": "sheet_c40",
        "sheet_number": "C-4.0",
        "sheet_title": "Utility Plan",
        "discipline": "utility",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "present",
        "file_name": "C-4.0-utility-plan.pdf",
        "sheet_purpose": (
            "Water main, gravity sewer, the sanitary pump station, and dry "
            "utilities."
        ),
        "related_documents": ["doc_utility_plan"],
        "related_checklist_items": ["chk_rfi_closure"],
        "related_findings": ["find_rfi_open"],
    },
    {
        "sheet_id": "sheet_c50",
        "sheet_number": "C-5.0",
        "sheet_title": "Erosion and Sediment Control Plan",
        "discipline": "erosion_control",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "present",
        "file_name": "C-5.0-erosion-sediment-control.pdf",
        "sheet_purpose": (
            "Silt fence, inlet protection, the stabilized construction "
            "entrance, and stabilization measures."
        ),
        "related_documents": ["doc_escp", "doc_swppp"],
        "related_checklist_items": ["chk_erosion_controls", "chk_escp_phasing"],
        "related_findings": ["find_escp_phasing"],
    },
    {
        "sheet_id": "sheet_c51",
        "sheet_number": "C-5.1",
        "sheet_title": "Construction Phasing and Erosion Control Details",
        "discipline": "erosion_control",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "needs_reviewer_confirmation",
        "file_name": "C-5.1-phasing-erosion-details.pdf",
        "sheet_purpose": (
            "Construction phasing and erosion control details cited by the "
            "erosion control plan; sequence notes appear incomplete."
        ),
        "related_documents": ["doc_escp", "doc_phasing_plan"],
        "related_checklist_items": ["chk_escp_phasing"],
        "related_findings": ["find_escp_phasing"],
    },
    {
        "sheet_id": "sheet_c60",
        "sheet_number": "C-6.0",
        "sheet_title": "Stormwater Management Details",
        "discipline": "details",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "present",
        "file_name": "C-6.0-stormwater-details.pdf",
        "sheet_purpose": (
            "Basin outlet structures, riprap aprons, and stormwater detail "
            "callouts."
        ),
        "related_documents": ["doc_stormwater_report"],
        "related_checklist_items": ["chk_outfall_identified"],
        "related_findings": [],
    },
    {
        "sheet_id": "sheet_c70",
        "sheet_number": "C-7.0",
        "sheet_title": "Roadway Profiles",
        "discipline": "profiles",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "present",
        "file_name": "C-7.0-roadway-profiles.pdf",
        "sheet_purpose": "Centerline profiles for Brookside Drive and Meadow Court.",
        "related_documents": ["doc_layout_plan"],
        "related_checklist_items": [],
        "related_findings": [],
    },
    {
        "sheet_id": "sheet_c80",
        "sheet_number": "C-8.0",
        "sheet_title": "Landscape and Buffer Plan",
        "discipline": "landscaping",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "present",
        "file_name": "C-8.0-landscape-buffer.pdf",
        "sheet_purpose": (
            "Landscaping, the wetland buffer, and planting near the stream "
            "corridor."
        ),
        "related_documents": ["doc_existing_conditions"],
        "related_checklist_items": [],
        "related_findings": [],
    },
    {
        "sheet_id": "sheet_d10",
        "sheet_number": "D-1.0",
        "sheet_title": "Construction Details",
        "discipline": "details",
        "revision": "0",
        "revision_date": "2026-04-02",
        "status": "present",
        "file_name": "D-1.0-construction-details.pdf",
        "sheet_purpose": "General construction details and standard notes.",
        "related_documents": [],
        "related_checklist_items": [],
        "related_findings": [],
    },
]


# CAD-aware feature metadata. Seeded, not extracted from DWG or DXF files.
CAD_METADATA = [
    {
        "cad_metadata_id": "cad_basin_a",
        "sheet_id": "sheet_c30",
        "source_type": "seeded_metadata",
        "entity_type": "basin",
        "entity_label": "Basin A",
        "layer_name": "C-STORM-BASIN",
        "discipline": "grading",
        "related_document_id": "doc_grading_drainage",
        "related_checklist_item_id": "chk_reference_consistency",
        "related_finding_id": "find_basin_naming",
        "notes": (
            "Label used on the grading plan and in the drainage calculations; "
            "conflicts with the stormwater report label Basin 1."
        ),
    },
    {
        "cad_metadata_id": "cad_basin_1",
        "sheet_id": "sheet_c30",
        "source_type": "report_reference",
        "entity_type": "basin",
        "entity_label": "Basin 1",
        "layer_name": "C-STORM-BASIN",
        "discipline": "drainage",
        "related_document_id": "doc_stormwater_report",
        "related_checklist_item_id": "chk_reference_consistency",
        "related_finding_id": "find_basin_naming",
        "notes": (
            "Wet detention basin label used in the stormwater report; the "
            "grading plan labels the same feature Basin A."
        ),
    },
    {
        "cad_metadata_id": "cad_meadow_infiltration_basin",
        "sheet_id": "sheet_c30",
        "source_type": "seeded_metadata",
        "entity_type": "basin",
        "entity_label": "Meadow infiltration basin",
        "layer_name": "C-STORM-BASIN",
        "discipline": "drainage",
        "related_document_id": "doc_stormwater_report",
        "related_checklist_item_id": "chk_infiltration_testing",
        "related_finding_id": "find_infiltration_missing",
        "notes": (
            "Proposed infiltration basin in the meadow; feasibility depends on "
            "infiltration testing and groundwater separation."
        ),
    },
    {
        "cad_metadata_id": "cad_wet_detention_basin",
        "sheet_id": "sheet_c30",
        "source_type": "seeded_metadata",
        "entity_type": "basin",
        "entity_label": "Wet detention basin",
        "layer_name": "C-STORM-BASIN",
        "discipline": "drainage",
        "related_document_id": "doc_oem_plan",
        "related_checklist_item_id": "chk_oem_owner",
        "related_finding_id": "find_oem_owner",
        "notes": (
            "Wet detention basin cited in the O&M plan; long-term maintenance "
            "ownership notes are unclear on the plan set."
        ),
    },
    {
        "cad_metadata_id": "cad_brookside_drive",
        "sheet_id": "sheet_c20",
        "source_type": "sheet_index",
        "entity_type": "road",
        "entity_label": "Brookside Drive",
        "layer_name": "C-ROAD-CNTR",
        "discipline": "layout",
        "related_document_id": "doc_layout_plan",
        "related_checklist_item_id": None,
        "related_finding_id": None,
        "notes": "Primary subdivision road serving the upland lots.",
    },
    {
        "cad_metadata_id": "cad_meadow_court",
        "sheet_id": "sheet_c20",
        "source_type": "sheet_index",
        "entity_type": "road",
        "entity_label": "Meadow Court",
        "layer_name": "C-ROAD-CNTR",
        "discipline": "layout",
        "related_document_id": "doc_layout_plan",
        "related_checklist_item_id": None,
        "related_finding_id": None,
        "notes": "Cul-de-sac serving the lower lots near the buffer.",
    },
    {
        "cad_metadata_id": "cad_quarry_road_culvert",
        "sheet_id": "sheet_c10",
        "source_type": "plan_note",
        "entity_type": "culvert",
        "entity_label": "Quarry Road culvert",
        "layer_name": "C-STORM-CULV",
        "discipline": "drainage",
        "related_document_id": "doc_existing_conditions",
        "related_checklist_item_id": "chk_downstream_capacity",
        "related_finding_id": "find_downstream_capacity",
        "notes": (
            "Existing 36-inch culvert and downstream discharge point under "
            "Quarry Road."
        ),
    },
    {
        "cad_metadata_id": "cad_outfall_1",
        "sheet_id": "sheet_c30",
        "source_type": "plan_note",
        "entity_type": "outfall",
        "entity_label": "Outfall 1",
        "layer_name": "C-STORM-OUTF",
        "discipline": "drainage",
        "related_document_id": "doc_inspection_notes",
        "related_checklist_item_id": "chk_inspection_closeout",
        "related_finding_id": "find_inspection_open",
        "notes": (
            "Basin outfall flagged in an inspection note for sediment; the "
            "corrective action is not shown on a current plan sheet."
        ),
    },
    {
        "cad_metadata_id": "cad_pipe_p12",
        "sheet_id": "sheet_c40",
        "source_type": "plan_note",
        "entity_type": "pipe",
        "entity_label": "Pipe P-12",
        "layer_name": "C-STORM-PIPE",
        "discipline": "utility",
        "related_document_id": "doc_rfi_log",
        "related_checklist_item_id": "chk_rfi_closure",
        "related_finding_id": "find_rfi_open",
        "notes": (
            "Storm drain pipe with an open RFI on pipe material; no material "
            "response is recorded in the RFI log."
        ),
    },
    {
        "cad_metadata_id": "cad_catch_basin_cb7",
        "sheet_id": "sheet_c30",
        "source_type": "seeded_metadata",
        "entity_type": "catch_basin",
        "entity_label": "Catch basin CB-7",
        "layer_name": "C-STORM-STRC",
        "discipline": "drainage",
        "related_document_id": "doc_grading_drainage",
        "related_checklist_item_id": None,
        "related_finding_id": None,
        "notes": "Curb inlet catch basin in the storm drain network.",
    },
    {
        "cad_metadata_id": "cad_wetland_buffer",
        "sheet_id": "sheet_c80",
        "source_type": "plan_note",
        "entity_type": "wetland_buffer",
        "entity_label": "Wetland buffer",
        "layer_name": "C-ENV-BUFR",
        "discipline": "landscaping",
        "related_document_id": "doc_existing_conditions",
        "related_checklist_item_id": "chk_outfall_identified",
        "related_finding_id": None,
        "notes": "100-ft town buffer along the southeast boundary near the stream.",
    },
    {
        "cad_metadata_id": "cad_construction_entrance",
        "sheet_id": "sheet_c50",
        "source_type": "seeded_metadata",
        "entity_type": "construction_entrance",
        "entity_label": "Construction entrance",
        "layer_name": "C-EROS-ENTR",
        "discipline": "erosion_control",
        "related_document_id": "doc_escp",
        "related_checklist_item_id": "chk_erosion_controls",
        "related_finding_id": None,
        "notes": "Stabilized construction entrance off Quarry Road.",
    },
    {
        "cad_metadata_id": "cad_silt_fence",
        "sheet_id": "sheet_c50",
        "source_type": "seeded_metadata",
        "entity_type": "erosion_control",
        "entity_label": "Silt fence",
        "layer_name": "C-EROS-SILT",
        "discipline": "erosion_control",
        "related_document_id": "doc_escp",
        "related_checklist_item_id": "chk_escp_phasing",
        "related_finding_id": "find_escp_phasing",
        "notes": "Perimeter silt fence along the downhill limits of disturbance.",
    },
    {
        "cad_metadata_id": "cad_pump_station",
        "sheet_id": "sheet_c40",
        "source_type": "seeded_metadata",
        "entity_type": "utility",
        "entity_label": "Utility pump station",
        "layer_name": "C-SSWR-PUMP",
        "discipline": "utility",
        "related_document_id": "doc_utility_plan",
        "related_checklist_item_id": None,
        "related_finding_id": None,
        "notes": "Sanitary pump station serving the low lots.",
    },
    {
        "cad_metadata_id": "cad_lot_17",
        "sheet_id": "sheet_c20",
        "source_type": "sheet_index",
        "entity_type": "lot",
        "entity_label": "Lot 17",
        "layer_name": "C-PROP-LOT",
        "discipline": "layout",
        "related_document_id": "doc_layout_plan",
        "related_checklist_item_id": None,
        "related_finding_id": None,
        "notes": "Upland lot on the loop road.",
    },
    {
        "cad_metadata_id": "cad_lot_33",
        "sheet_id": "sheet_c20",
        "source_type": "sheet_index",
        "entity_type": "lot",
        "entity_label": "Lot 33",
        "layer_name": "C-PROP-LOT",
        "discipline": "layout",
        "related_document_id": "doc_layout_plan",
        "related_checklist_item_id": None,
        "related_finding_id": None,
        "notes": "Lower lot on Meadow Court near the buffer.",
    },
]


# Plan references connecting documents, sheets, and civil features. The
# consistency_status on each reference is the seeded evaluation outcome. The
# non-consistent references drive the plan consistency findings.
PLAN_REFERENCES = [
    {
        "plan_reference_id": "pref_report_c30",
        "source_type": "document",
        "source_id": "doc_stormwater_report",
        "target_type": "plan_sheet",
        "target_id": "sheet_c30",
        "reference_label": "Stormwater report cites Grading and Drainage Plan C-3.0",
        "reference_context": (
            "The stormwater report references sheet C-3.0 for basin locations "
            "and the storm drain network."
        ),
        "consistency_status": "consistent",
        "review_note": "Referenced sheet C-3.0 is present in the package.",
    },
    {
        "plan_reference_id": "pref_report_c31",
        "source_type": "document",
        "source_id": "doc_stormwater_report",
        "target_type": "plan_sheet",
        "target_id": "sheet_c31",
        "reference_label": "Stormwater report cites revised grading sheet C-3.1",
        "reference_context": (
            "The narrative and report cite a revised grading sheet C-3.1 that is "
            "not included in the submitted package."
        ),
        "consistency_status": "missing_target",
        "review_note": "Referenced sheet C-3.1 is not included in the package.",
    },
    {
        "plan_reference_id": "pref_calcs_basin_a",
        "source_type": "document",
        "source_id": "doc_hydrology_calcs",
        "target_type": "cad_feature",
        "target_id": "cad_basin_a",
        "reference_label": "Drainage calculations reference Basin A",
        "reference_context": (
            "The drainage calculations and grading plan label the wet detention "
            "basin Basin A, while the stormwater report labels it Basin 1."
        ),
        "consistency_status": "conflicting_label",
        "review_note": (
            "Basin A and Basin 1 appear to describe the same feature with "
            "conflicting labels."
        ),
    },
    {
        "plan_reference_id": "pref_grading_basin_1",
        "source_type": "plan_sheet",
        "source_id": "sheet_c30",
        "target_type": "cad_feature",
        "target_id": "cad_basin_1",
        "reference_label": "Grading plan references Basin 1",
        "reference_context": (
            "The grading plan locates the wet detention basin referred to as "
            "Basin 1 in the stormwater report."
        ),
        "consistency_status": "consistent",
        "review_note": "Basin location is shown on the grading plan.",
    },
    {
        "plan_reference_id": "pref_oem_wet_basin",
        "source_type": "document",
        "source_id": "doc_oem_plan",
        "target_type": "cad_feature",
        "target_id": "cad_wet_detention_basin",
        "reference_label": "O&M plan references wet detention basin maintenance",
        "reference_context": (
            "The O&M plan references wet detention basin maintenance, but plan "
            "sheet ownership notes for the facility are unclear."
        ),
        "consistency_status": "needs_human_review",
        "review_note": (
            "Maintenance ownership for the wet detention basin is not clearly "
            "documented on the plan set."
        ),
    },
    {
        "plan_reference_id": "pref_escp_entrance",
        "source_type": "document",
        "source_id": "doc_escp",
        "target_type": "cad_feature",
        "target_id": "cad_construction_entrance",
        "reference_label": "Erosion control plan references construction entrance",
        "reference_context": (
            "The erosion and sediment control plan references the stabilized "
            "construction entrance shown on sheet C-5.0."
        ),
        "consistency_status": "consistent",
        "review_note": "Construction entrance is shown on sheet C-5.0.",
    },
    {
        "plan_reference_id": "pref_inspection_outfall",
        "source_type": "document",
        "source_id": "doc_inspection_notes",
        "target_type": "cad_feature",
        "target_id": "cad_outfall_1",
        "reference_label": "Inspection note references Outfall 1",
        "reference_context": (
            "An inspection note flags sediment at Outfall 1, but the corrective "
            "action is not shown on a current plan sheet."
        ),
        "consistency_status": "missing_target",
        "review_note": (
            "Corrective action for Outfall 1 is not located on a current plan "
            "sheet."
        ),
    },
    {
        "plan_reference_id": "pref_rfi_pipe_p12",
        "source_type": "document",
        "source_id": "doc_rfi_log",
        "target_type": "cad_feature",
        "target_id": "cad_pipe_p12",
        "reference_label": "RFI log references Pipe P-12",
        "reference_context": (
            "The RFI log references Pipe P-12 and asks about pipe material, but "
            "no material response is recorded."
        ),
        "consistency_status": "missing_target",
        "review_note": "Pipe P-12 material response is missing from the RFI log.",
    },
    {
        "plan_reference_id": "pref_utility_pump",
        "source_type": "document",
        "source_id": "doc_utility_plan",
        "target_type": "cad_feature",
        "target_id": "cad_pump_station",
        "reference_label": "Utility plan references the pump station",
        "reference_context": (
            "The utility plan locates the sanitary pump station serving the low "
            "lots."
        ),
        "consistency_status": "consistent",
        "review_note": "Pump station is shown on sheet C-4.0.",
    },
    {
        "plan_reference_id": "pref_layout_meadow_court",
        "source_type": "document",
        "source_id": "doc_layout_plan",
        "target_type": "cad_feature",
        "target_id": "cad_meadow_court",
        "reference_label": "Layout plan references Meadow Court",
        "reference_context": (
            "The layout plan locates the Meadow Court cul-de-sac serving the "
            "lower lots."
        ),
        "consistency_status": "consistent",
        "review_note": "Meadow Court is shown on sheet C-2.0.",
    },
    {
        "plan_reference_id": "pref_escp_c51",
        "source_type": "document",
        "source_id": "doc_escp",
        "target_type": "plan_sheet",
        "target_id": "sheet_c51",
        "reference_label": "Erosion control phasing references Sheet C-5.1",
        "reference_context": (
            "The erosion control plan references Sheet C-5.1 for construction "
            "sequencing, but the sequence notes are incomplete or unclear."
        ),
        "consistency_status": "unclear",
        "review_note": (
            "Construction sequence notes on Sheet C-5.1 are incomplete or "
            "unclear and need reviewer confirmation."
        ),
    },
]


# Phase 7 sheet hotspots. Each hotspot is a seeded review-support annotation
# placed over a synthetic plan sheet preview using percentage coordinates. The
# related_plan_finding_ids use the deterministic id form plan_find_<reference_id>
# produced by the plan consistency service. None of this is extracted CAD data.
PLAN_SHEET_HOTSPOTS = [
    {
        "hotspot_id": "hs_c30_missing_c31",
        "sheet_id": "sheet_c30",
        "hotspot_type": "missing_referenced_sheet",
        "label": "Revised sheet C-3.1 referenced but not included",
        "description": (
            "The grading and narrative cite a revised grading sheet C-3.1 that "
            "is not in the package. Confirm the revised sheet is submitted "
            "before relying on this grading area."
        ),
        "x_percent": 8.0,
        "y_percent": 10.0,
        "width_percent": 26.0,
        "height_percent": 12.0,
        "severity": "high",
        "related_plan_reference_ids": ["pref_report_c31"],
        "related_cad_metadata_ids": [],
        "related_plan_finding_ids": ["plan_find_pref_report_c31"],
        "related_document_ids": ["doc_site_narrative", "doc_revised_c31"],
        "related_checklist_item_ids": ["chk_referenced_sheets_present"],
        "review_note": (
            "Referenced revised grading sheet is missing from the submitted "
            "package."
        ),
        "requires_human_review": True,
    },
    {
        "hotspot_id": "hs_c30_basin_conflict",
        "sheet_id": "sheet_c30",
        "hotspot_type": "basin_label_conflict",
        "label": "Basin label conflict: Basin A vs Basin 1",
        "description": (
            "The grading plan and drainage calculations label the wet "
            "detention basin Basin A, while the stormwater report labels the "
            "same feature Basin 1. Confirm a single consistent label."
        ),
        "x_percent": 54.0,
        "y_percent": 58.0,
        "width_percent": 22.0,
        "height_percent": 16.0,
        "severity": "medium",
        "related_plan_reference_ids": ["pref_calcs_basin_a"],
        "related_cad_metadata_ids": ["cad_basin_a", "cad_basin_1"],
        "related_plan_finding_ids": ["plan_find_pref_calcs_basin_a"],
        "related_document_ids": [
            "doc_grading_drainage",
            "doc_stormwater_report",
        ],
        "related_checklist_item_ids": ["chk_reference_consistency"],
        "review_note": (
            "Conflicting basin labels across the plan set and report need a "
            "single consistent label."
        ),
        "requires_human_review": True,
    },
    {
        "hotspot_id": "hs_c30_wet_basin_oem",
        "sheet_id": "sheet_c30",
        "hotspot_type": "maintenance_ownership",
        "label": "Wet detention basin maintenance ownership unclear",
        "description": (
            "The O&M plan references wet detention basin maintenance, but plan "
            "sheet ownership notes for the facility are unclear. Confirm the "
            "responsible maintenance party."
        ),
        "x_percent": 60.0,
        "y_percent": 30.0,
        "width_percent": 20.0,
        "height_percent": 12.0,
        "severity": "high",
        "related_plan_reference_ids": ["pref_oem_wet_basin"],
        "related_cad_metadata_ids": ["cad_wet_detention_basin"],
        "related_plan_finding_ids": ["plan_find_pref_oem_wet_basin"],
        "related_document_ids": ["doc_oem_plan"],
        "related_checklist_item_ids": ["chk_oem_owner"],
        "review_note": (
            "Maintenance ownership for the wet detention basin is not clearly "
            "documented on the plan set."
        ),
        "requires_human_review": True,
    },
    {
        "hotspot_id": "hs_c40_pipe_p12",
        "sheet_id": "sheet_c40",
        "hotspot_type": "pipe_reference",
        "label": "Pipe P-12 material response missing",
        "description": (
            "The RFI log references Pipe P-12 and asks about pipe material, but "
            "no material response is recorded. Confirm the pipe material before "
            "relying on this segment."
        ),
        "x_percent": 30.0,
        "y_percent": 44.0,
        "width_percent": 24.0,
        "height_percent": 10.0,
        "severity": "medium",
        "related_plan_reference_ids": ["pref_rfi_pipe_p12"],
        "related_cad_metadata_ids": ["cad_pipe_p12"],
        "related_plan_finding_ids": ["plan_find_pref_rfi_pipe_p12"],
        "related_document_ids": ["doc_rfi_log"],
        "related_checklist_item_ids": ["chk_rfi_closure"],
        "review_note": "Open RFI on Pipe P-12 material has no recorded response.",
        "requires_human_review": True,
    },
    {
        "hotspot_id": "hs_c60_outfall_detail",
        "sheet_id": "sheet_c60",
        "hotspot_type": "basin_outlet_detail",
        "label": "Outfall 1 corrective action not shown",
        "description": (
            "An inspection note flags sediment at Outfall 1, but the corrective "
            "action is not shown on a current plan sheet. Confirm where the "
            "corrective action is documented."
        ),
        "x_percent": 18.0,
        "y_percent": 62.0,
        "width_percent": 22.0,
        "height_percent": 14.0,
        "severity": "high",
        "related_plan_reference_ids": ["pref_inspection_outfall"],
        "related_cad_metadata_ids": ["cad_outfall_1"],
        "related_plan_finding_ids": ["plan_find_pref_inspection_outfall"],
        "related_document_ids": ["doc_inspection_notes"],
        "related_checklist_item_ids": ["chk_inspection_closeout"],
        "review_note": (
            "Corrective action for the Outfall 1 sediment note is not located "
            "on a current plan sheet."
        ),
        "requires_human_review": True,
    },
    {
        "hotspot_id": "hs_c51_unclear_phasing",
        "sheet_id": "sheet_c51",
        "hotspot_type": "unclear_revision",
        "label": "Construction sequence notes unclear on C-5.1",
        "description": (
            "The erosion control plan references Sheet C-5.1 for construction "
            "sequencing, but the sequence notes are incomplete or unclear. "
            "Request clarified sequence notes."
        ),
        "x_percent": 40.0,
        "y_percent": 20.0,
        "width_percent": 28.0,
        "height_percent": 14.0,
        "severity": "medium",
        "related_plan_reference_ids": ["pref_escp_c51"],
        "related_cad_metadata_ids": [],
        "related_plan_finding_ids": ["plan_find_pref_escp_c51"],
        "related_document_ids": ["doc_escp", "doc_phasing_plan"],
        "related_checklist_item_ids": ["chk_escp_phasing"],
        "review_note": (
            "Construction sequence notes on Sheet C-5.1 are incomplete or "
            "unclear."
        ),
        "requires_human_review": True,
    },
    {
        "hotspot_id": "hs_c50_construction_entrance",
        "sheet_id": "sheet_c50",
        "hotspot_type": "erosion_control_detail",
        "label": "Construction entrance and silt fence detail review",
        "description": (
            "The stabilized construction entrance and perimeter silt fence are "
            "shown on the erosion control plan. Confirm the details align with "
            "the construction sequencing on Sheet C-5.1."
        ),
        "x_percent": 12.0,
        "y_percent": 70.0,
        "width_percent": 24.0,
        "height_percent": 12.0,
        "severity": "low",
        "related_plan_reference_ids": ["pref_escp_entrance"],
        "related_cad_metadata_ids": ["cad_construction_entrance", "cad_silt_fence"],
        "related_plan_finding_ids": ["plan_find_pref_escp_c51"],
        "related_document_ids": ["doc_escp"],
        "related_checklist_item_ids": ["chk_erosion_controls"],
        "review_note": (
            "Erosion control entrance and silt fence details to confirm against "
            "phasing."
        ),
        "requires_human_review": True,
    },
    {
        "hotspot_id": "hs_c80_wetland_buffer",
        "sheet_id": "sheet_c80",
        "hotspot_type": "wetland_buffer_setback",
        "label": "Wetland buffer setback near outfall",
        "description": (
            "The 100-ft town wetland buffer runs along the southeast boundary "
            "near the stream and an outfall. Confirm proposed work respects the "
            "buffer setback."
        ),
        "x_percent": 66.0,
        "y_percent": 72.0,
        "width_percent": 26.0,
        "height_percent": 16.0,
        "severity": "medium",
        "related_plan_reference_ids": [],
        "related_cad_metadata_ids": ["cad_wetland_buffer"],
        "related_plan_finding_ids": [],
        "related_document_ids": ["doc_existing_conditions"],
        "related_checklist_item_ids": ["chk_outfall_identified"],
        "review_note": (
            "Wetland buffer setback near the outfall needs reviewer "
            "confirmation."
        ),
        "requires_human_review": True,
    },
]


def plan_data_is_loaded(db: Session) -> bool:
    """Return True if plan sheets are already seeded for the project."""

    stmt = select(models.PlanSheet).where(
        models.PlanSheet.project_id == PROJECT_ID
    )
    return db.scalars(stmt).first() is not None


def seed_plansheets(db: Session, *, force: bool = False) -> None:
    """Seed plan sheets, CAD metadata, plan references, and findings.

    If the plan data already exists and force is False, seeding is skipped so
    the operation is idempotent. With force=True, existing plan rows are removed
    first and reloaded. After seeding the raw tables, the plan consistency
    service is run once so the consistency findings exist immediately.
    """

    # Imported here to avoid a circular import at module load time.
    from app.services import plan_consistency_service

    if plan_data_is_loaded(db):
        if not force:
            return
        for model in (
            models.PlanConsistencyReviewAction,
            models.PlanSheetHotspot,
            models.PlanConsistencyFinding,
            models.PlanReference,
            models.CadMetadata,
            models.PlanSheet,
        ):
            db.query(model).filter_by(project_id=PROJECT_ID).delete()
        db.commit()

    db.add_all(
        models.PlanSheet(project_id=PROJECT_ID, **sheet) for sheet in PLAN_SHEETS
    )
    db.add_all(
        models.CadMetadata(project_id=PROJECT_ID, **record)
        for record in CAD_METADATA
    )
    db.add_all(
        models.PlanReference(project_id=PROJECT_ID, **ref)
        for ref in PLAN_REFERENCES
    )
    db.commit()

    # Generate the plan consistency findings from the seeded references and
    # sheets so the findings endpoints return data immediately after seeding.
    plan_consistency_service.run_consistency_check(db, PROJECT_ID)

    # Seed the Phase 7 sheet hotspots after the findings exist, since hotspots
    # reference plan consistency findings.
    db.add_all(
        models.PlanSheetHotspot(project_id=PROJECT_ID, **hotspot)
        for hotspot in PLAN_SHEET_HOTSPOTS
    )
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_plan_{uuid.uuid4().hex[:12]}",
            project_id=PROJECT_ID,
            event_type="sheet_hotspot_review_data_seeded",
            actor_type="system",
            related_entity_type="plan_sheet_hotspots",
            related_entity_id=PROJECT_ID,
            description=(
                f"Seeded {len(PLAN_SHEET_HOTSPOTS)} plan sheet hotspots as "
                "review-support annotations, not extracted CAD geometry."
            ),
            timestamp=datetime.now(timezone.utc),
            event_metadata={"hotspot_count": len(PLAN_SHEET_HOTSPOTS)},
        )
    )
    db.commit()


def main() -> None:
    """Create tables and load the plan data. Used by python -m app.db.seed_plansheets."""

    init_db()
    db = SessionLocal()
    try:
        seed_plansheets(db, force=True)
        print(
            "Seeded Brookside Meadows plan data: "
            f"{len(PLAN_SHEETS)} plan sheets, {len(CAD_METADATA)} CAD metadata "
            f"records, {len(PLAN_REFERENCES)} plan references, "
            f"{len(PLAN_SHEET_HOTSPOTS)} sheet hotspots."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
