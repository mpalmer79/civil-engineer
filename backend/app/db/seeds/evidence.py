"""Seed source evidence for the Brookside Meadows fixture.

Phase 3 seeds short, synthetic document chunks (not full documents), source
evidence records that link chunks to the ten expected review-support findings,
and a few representative retrieval queries for auditing.

These excerpts are realistic but synthetic. They do not reproduce any real
private engineering document. The chunks intentionally carry the evidence (and
the gaps) behind the planted review issues so keyword retrieval has something to
surface. None of this content is a final engineering conclusion.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import models
from app.db.seeds.documents import DOCUMENTS
from app.db.seeds.reference_project import PROJECT_ID

# Lookup for document type and file name so chunks stay consistent with the
# canonical document seed.
_DOC_META = {
    doc["document_id"]: (doc["document_type"], doc["file_name"])
    for doc in DOCUMENTS
}


def _chunk(
    chunk_id: str,
    document_id: str,
    page: int | None,
    section: str | None,
    index: int,
    content: str,
    keywords: list[str],
    checklist: list[str],
    findings: list[str],
) -> dict:
    document_type, file_name = _DOC_META[document_id]
    return {
        "chunk_id": chunk_id,
        "project_id": PROJECT_ID,
        "document_id": document_id,
        "document_type": document_type,
        "file_name": file_name,
        "page_number": page,
        "section_heading": section,
        "chunk_index": index,
        "content": content,
        "keywords": keywords,
        "related_checklist_items": checklist,
        "related_findings": findings,
        "chunk_origin": "seeded_demo",
    }


CHUNKS: list[dict] = [
    # Site plan narrative
    _chunk(
        "chunk_site_001", "doc_site_narrative", 1, "Project Overview", 0,
        "Brookside Meadows proposes 47 single-family lots on a 38.5-acre former "
        "farm parcel served by a new internal road network and shared stormwater "
        "facilities.",
        ["project", "lots", "subdivision", "stormwater"],
        ["chk_pkg_completeness"], [],
    ),
    _chunk(
        "chunk_site_002", "doc_site_narrative", 2, "Stormwater Strategy", 1,
        "The stormwater strategy combines bioretention and an infiltration basin "
        "with a wet detention basin discharging toward the Quarry Road culvert.",
        ["stormwater", "bioretention", "infiltration basin", "detention basin"],
        ["chk_bmp_identified"], [],
    ),
    _chunk(
        "chunk_site_003", "doc_site_narrative", 2, "Maintenance", 2,
        "Long-term maintenance of the shared stormwater facilities is intended "
        "to be handled by the future homeowners association.",
        ["maintenance", "hoa", "operation and maintenance", "owner"],
        ["chk_oem_owner"], ["find_oem_owner"],
    ),
    _chunk(
        "chunk_site_004", "doc_site_narrative", 3, "Plan Set References", 3,
        "Grading revisions are shown on revised sheet C-3.1, noted as included "
        "under separate cover with this submission.",
        ["revised sheet", "c-3.1", "grading", "plan set"],
        ["chk_referenced_sheets_present"], ["find_missing_sheet"],
    ),
    # Existing conditions plan
    _chunk(
        "chunk_exist_001", "doc_existing_conditions", 1, "Topography", 0,
        "Existing grades fall from about 412 ft in the northwest to about 358 ft "
        "near the southeast corner toward Brook Run.",
        ["topography", "grading", "slope"],
        ["chk_drainage_areas"], [],
    ),
    _chunk(
        "chunk_exist_002", "doc_existing_conditions", 1, "Drainage Path", 1,
        "Existing runoff sheet flows to the southeast and discharges through an "
        "existing 36-inch culvert under Quarry Road.",
        ["culvert", "quarry road", "drainage path", "downstream"],
        ["chk_downstream_capacity"], ["find_downstream_capacity"],
    ),
    _chunk(
        "chunk_exist_003", "doc_existing_conditions", 2, "Wetland and Stream", 2,
        "A delineated wetland and intermittent stream (Brook Run) occupy the "
        "southeast boundary, with a 100-ft town buffer.",
        ["wetland", "stream", "buffer", "brook run"],
        ["chk_outfall_identified"], [],
    ),
    # Layout plan
    _chunk(
        "chunk_layout_001", "doc_layout_plan", 1, "Lot Layout", 0,
        "The plan shows 47 lots served by Brookside Drive, a loop road, and the "
        "Meadow Court cul-de-sac.",
        ["lots", "road", "cul-de-sac"],
        ["chk_drainage_areas"], [],
    ),
    _chunk(
        "chunk_layout_002", "doc_layout_plan", 1, "Impervious Area", 1,
        "Proposed rooftops, driveways, and roadway add impervious area tributary "
        "to the storm drain network.",
        ["impervious", "runoff", "storm drain"],
        ["chk_runoff_calcs"], [],
    ),
    _chunk(
        "chunk_layout_003", "doc_layout_plan", 2, "Sidewalks", 2,
        "A sidewalk is provided along one side of Brookside Drive with a path "
        "connection to open space.",
        ["sidewalk", "pedestrian"],
        [], [],
    ),
    # Grading and drainage plan
    _chunk(
        "chunk_grade_001", "doc_grading_drainage", 1, "Grading Plan", 0,
        "Proposed grading directs road runoff to curb inlets and the storm drain "
        "network toward the basins.",
        ["grading", "storm drain", "inlets"],
        ["chk_bmp_identified"], [],
    ),
    _chunk(
        "chunk_grade_002", "doc_grading_drainage", 2, "Pond A", 1,
        "Pond A is the wet detention basin in the southeast low area providing "
        "peak-flow attenuation before the culvert outfall.",
        ["pond a", "detention basin", "basin", "outfall"],
        ["chk_reference_consistency", "chk_bmp_identified"],
        ["find_basin_naming"],
    ),
    _chunk(
        "chunk_grade_003", "doc_grading_drainage", 2, "Outlet Protection", 2,
        "Riprap outlet protection is provided at the Pond A outlet and the "
        "culvert headwall.",
        ["riprap", "outlet protection", "outfall"],
        ["chk_outfall_identified"], [],
    ),
    _chunk(
        "chunk_grade_004", "doc_grading_drainage", 3, "Infiltration Basin", 3,
        "The infiltration basin (Basin 2) is graded into the meadow to promote "
        "recharge.",
        ["infiltration basin", "basin 2", "recharge"],
        ["chk_infiltration_testing"], [],
    ),
    # Utility plan
    _chunk(
        "chunk_util_001", "doc_utility_plan", 1, "Water and Sewer", 0,
        "A water main extension and gravity sanitary sewer serve the lots, with a "
        "pump station for the low lots.",
        ["water main", "sewer", "pump station", "utility"],
        [], [],
    ),
    _chunk(
        "chunk_util_002", "doc_utility_plan", 2, "Storm Crossings", 1,
        "Storm drain crossings of the sanitary sewer are shown near the "
        "cul-de-sac.",
        ["storm drain", "crossing", "sewer"],
        [], [],
    ),
    _chunk(
        "chunk_util_003", "doc_utility_plan", 2, "Pipe Material", 2,
        "Storm drain pipe material is shown as reinforced concrete pipe, pending "
        "confirmation against the open RFI.",
        ["pipe material", "rcp", "storm drain", "rfi"],
        ["chk_rfi_closure"], ["find_rfi_open"],
    ),
    # Stormwater management report
    _chunk(
        "chunk_swm_001", "doc_stormwater_report", 2, "Design Storm", 0,
        "Hydrologic analysis uses the 25-year, 24-hour design storm for "
        "peak-flow attenuation sizing.",
        ["design storm", "25-year", "peak flow"],
        ["chk_design_storm_stated", "chk_design_storm_consistent"],
        ["find_storm_conflict"],
    ),
    _chunk(
        "chunk_swm_002", "doc_stormwater_report", 3, "Basin 1", 1,
        "Basin 1, the wet detention basin, is sized to attenuate post-development "
        "peak flows before discharge.",
        ["basin 1", "detention basin", "basin"],
        ["chk_reference_consistency"], ["find_basin_naming"],
    ),
    _chunk(
        "chunk_swm_003", "doc_stormwater_report", 4, "Infiltration Basin", 2,
        "An infiltration basin (Basin 2) provides runoff volume reduction; "
        "infiltration testing is noted as to be provided under separate cover.",
        ["infiltration basin", "infiltration testing", "recharge"],
        ["chk_infiltration_testing"], ["find_infiltration_missing"],
    ),
    _chunk(
        "chunk_swm_004", "doc_stormwater_report", 4, "Water Quality", 3,
        "Bioretention cells BR-1 and BR-2 provide water-quality treatment of road "
        "runoff.",
        ["bioretention", "water quality", "treatment"],
        ["chk_bmp_identified"], [],
    ),
    _chunk(
        "chunk_swm_005", "doc_stormwater_report", 5, "Groundwater", 4,
        "The report does not include a separation analysis between the "
        "infiltration basin bottom and seasonal high groundwater.",
        ["groundwater", "separation", "infiltration"],
        ["chk_groundwater_separation"], ["find_gw_separation"],
    ),
    # Hydrology calculations
    _chunk(
        "chunk_hydro_001", "doc_hydrology_calcs", 1, "Curve Numbers", 0,
        "Existing and proposed curve numbers and times of concentration are "
        "tabulated by drainage area.",
        ["curve number", "time of concentration", "runoff"],
        ["chk_runoff_calcs", "chk_drainage_areas"], [],
    ),
    _chunk(
        "chunk_hydro_002", "doc_hydrology_calcs", 2, "Peak Flows", 1,
        "Proposed peak flows are computed for the 2, 10, and 25-year events at "
        "the basin inflow points.",
        ["peak flow", "design storm", "hydrology"],
        ["chk_runoff_calcs"], [],
    ),
    _chunk(
        "chunk_hydro_003", "doc_hydrology_calcs", 2, "Drainage Areas", 2,
        "Drainage area boundaries are delineated for existing and proposed "
        "conditions.",
        ["drainage area", "subcatchment"],
        ["chk_drainage_areas"], [],
    ),
    # Hydraulic calculations
    _chunk(
        "chunk_hyd_001", "doc_hydraulic_calcs", 1, "Pipe Sizing", 0,
        "Storm drain pipes are sized for the proposed peak flows with capacity "
        "checks at each run.",
        ["pipe sizing", "capacity", "storm drain"],
        [], [],
    ),
    _chunk(
        "chunk_hyd_002", "doc_hydraulic_calcs", 2, "Outlet Structure", 1,
        "The Basin 1 outlet structure is sized to control the post-development "
        "release rate.",
        ["outlet structure", "release rate", "basin 1"],
        ["chk_outfall_identified"], [],
    ),
    _chunk(
        "chunk_hyd_003", "doc_hydraulic_calcs", 2, "Analysis Limits", 2,
        "Hydraulic analysis is limited to onsite conveyance; downstream culvert "
        "capacity at Quarry Road is not evaluated in this submission.",
        ["downstream", "culvert", "capacity", "quarry road"],
        ["chk_downstream_capacity"], ["find_downstream_capacity"],
    ),
    # Soils and geotechnical report
    _chunk(
        "chunk_soil_001", "doc_soils_report", 2, "Soil Groups", 0,
        "Test pits indicate hydrologic soil groups B and C with a slower-draining "
        "C/D band in the lower meadow.",
        ["soil group", "hydrologic soil", "infiltration"],
        ["chk_soil_groundwater_doc"], [],
    ),
    _chunk(
        "chunk_soil_002", "doc_soils_report", 3, "Borings", 1,
        "Boring logs and test pit logs are provided for representative locations "
        "across the site.",
        ["boring", "test pit", "geotechnical"],
        ["chk_soil_groundwater_doc"], [],
    ),
    _chunk(
        "chunk_soil_003", "doc_soils_report", 4, "Seasonal High Groundwater", 2,
        "Seasonal high groundwater was observed within about 2.5 to 3.5 ft of "
        "existing grade in the lower meadow test pit area.",
        ["seasonal high groundwater", "groundwater", "water table"],
        ["chk_groundwater_separation", "chk_soil_groundwater_doc"],
        ["find_gw_separation"],
    ),
    _chunk(
        "chunk_soil_004", "doc_soils_report", 5, "Infiltration Feasibility", 3,
        "Field infiltration testing was not performed as part of this "
        "geotechnical scope; rates should be confirmed before infiltration "
        "design.",
        ["infiltration testing", "infiltration rate", "feasibility"],
        ["chk_infiltration_testing"], ["find_infiltration_missing"],
    ),
    # Erosion and sediment control plan
    _chunk(
        "chunk_escp_001", "doc_escp", 1, "Perimeter Controls", 0,
        "Silt fence is shown along the downhill limits of disturbance near the "
        "wetland buffer.",
        ["silt fence", "perimeter control", "erosion"],
        ["chk_erosion_controls"], [],
    ),
    _chunk(
        "chunk_escp_002", "doc_escp", 1, "Inlet Protection", 1,
        "Inlet protection is provided at catch basins, with a stabilized "
        "construction entrance off Quarry Road.",
        ["inlet protection", "construction entrance", "sediment"],
        ["chk_erosion_controls"], [],
    ),
    _chunk(
        "chunk_escp_003", "doc_escp", 2, "Stabilization", 2,
        "Temporary and permanent stabilization measures are specified for "
        "disturbed areas.",
        ["stabilization", "seeding", "erosion"],
        ["chk_erosion_controls"], [],
    ),
    _chunk(
        "chunk_escp_004", "doc_escp", 2, "Sequencing", 3,
        "The plan presents controls as a single build-out and does not tie "
        "control installation to the two construction phases.",
        ["phasing", "sequencing", "erosion control"],
        ["chk_escp_phasing"], ["find_escp_phasing"],
    ),
    # SWPPP
    _chunk(
        "chunk_swppp_001", "doc_swppp", 1, "Controls", 0,
        "The SWPPP describes erosion and sediment controls and pollution "
        "prevention practices for the construction phase.",
        ["swppp", "controls", "pollution prevention"],
        ["chk_erosion_controls"], [],
    ),
    _chunk(
        "chunk_swppp_002", "doc_swppp", 2, "Inspections", 1,
        "Inspection commitments include routine inspections and inspections after "
        "qualifying storm events.",
        ["inspection", "swppp", "frequency"],
        ["chk_inspection_closeout"], [],
    ),
    _chunk(
        "chunk_swppp_003", "doc_swppp", 2, "Corrective Action", 2,
        "A corrective action procedure is described for deficiencies identified "
        "during inspections.",
        ["corrective action", "deficiency", "inspection"],
        ["chk_inspection_closeout"], [],
    ),
    # Operation and maintenance plan
    _chunk(
        "chunk_oem_001", "doc_oem_plan", 1, "Maintenance Tasks", 0,
        "Routine maintenance tasks and inspection frequencies are listed for the "
        "detention basin, infiltration basin, and bioretention cells.",
        ["maintenance", "operation and maintenance", "tasks"],
        ["chk_oem_plan"], [],
    ),
    _chunk(
        "chunk_oem_002", "doc_oem_plan", 2, "Access", 1,
        "Maintenance access routes to the basins are identified.",
        ["access", "maintenance"],
        ["chk_oem_plan"], [],
    ),
    _chunk(
        "chunk_oem_003", "doc_oem_plan", 2, "Responsibility", 2,
        "The plan references HOA maintenance but does not include a recorded "
        "agreement binding the homeowners association to the work.",
        ["hoa", "responsibility", "operation and maintenance", "owner"],
        ["chk_oem_owner"], ["find_oem_owner"],
    ),
    _chunk(
        "chunk_oem_004", "doc_oem_plan", 3, "Funding", 3,
        "A long-term funding mechanism for maintenance is not specified.",
        ["funding", "maintenance", "hoa"],
        ["chk_oem_owner"], ["find_oem_owner"],
    ),
    # Construction phasing plan
    _chunk(
        "chunk_phase_001", "doc_phasing_plan", 1, "Phasing Concept", 0,
        "Construction is proposed in two phases: upland lots first, then the "
        "lower meadow lots and basins.",
        ["phasing", "construction sequence", "phases"],
        ["chk_escp_phasing"], ["find_escp_phasing"],
    ),
    _chunk(
        "chunk_phase_002", "doc_phasing_plan", 1, "Phase 1", 1,
        "Phase 1 includes the main road, upland lots, and the temporary sediment "
        "trap.",
        ["phase 1", "sediment trap", "upland"],
        ["chk_escp_phasing"], [],
    ),
    _chunk(
        "chunk_phase_003", "doc_phasing_plan", 2, "Phase 2", 2,
        "Phase 2 includes the lower lots, the wet detention basin, and the "
        "infiltration basin.",
        ["phase 2", "detention basin", "infiltration basin"],
        [], [],
    ),
    # Inspection notes
    _chunk(
        "chunk_insp_001", "doc_inspection_notes", 1, "Site Visit", 0,
        "A site visit recorded general construction progress and erosion control "
        "conditions.",
        ["inspection", "site visit", "erosion control"],
        ["chk_inspection_closeout"], [],
    ),
    _chunk(
        "chunk_insp_002", "doc_inspection_notes", 1, "Observation", 1,
        "Sediment accumulation was observed at the basin outlet during the "
        "inspection.",
        ["sediment", "basin outlet", "inspection", "deficiency"],
        ["chk_inspection_closeout"], ["find_inspection_open"],
    ),
    _chunk(
        "chunk_insp_003", "doc_inspection_notes", 2, "Status", 2,
        "No corrective action entry or closeout was recorded for the observed "
        "sediment at the outlet.",
        ["corrective action", "closeout", "sediment"],
        ["chk_inspection_closeout"], ["find_inspection_open"],
    ),
    # RFI log
    _chunk(
        "chunk_rfi_001", "doc_rfi_log", 1, "RFI Index", 0,
        "The RFI log lists open and closed requests for information for the "
        "project.",
        ["rfi", "log", "request for information"],
        ["chk_rfi_closure"], [],
    ),
    _chunk(
        "chunk_rfi_002", "doc_rfi_log", 1, "RFI-07", 1,
        "RFI-07 asks whether storm drain pipe should be reinforced concrete or "
        "HDPE.",
        ["rfi", "pipe material", "hdpe", "rcp"],
        ["chk_rfi_closure"], ["find_rfi_open"],
    ),
    _chunk(
        "chunk_rfi_003", "doc_rfi_log", 1, "RFI-07 Status", 2,
        "RFI-07 is shown as open with no recorded response.",
        ["rfi", "open", "no response", "pipe material"],
        ["chk_rfi_closure"], ["find_rfi_open"],
    ),
    # Municipal checklist
    _chunk(
        "chunk_muni_001", "doc_municipal_checklist", 1, "Required Submittals", 0,
        "The town checklist requires a stormwater report, drainage calculations, "
        "soils report, and an operation and maintenance plan.",
        ["checklist", "required", "submittal"],
        ["chk_pkg_completeness"], [],
    ),
    _chunk(
        "chunk_muni_002", "doc_municipal_checklist", 1, "Design Storm Standard", 1,
        "The town standard requires analysis of the 2, 10, and 100-year design "
        "storms for post-development conditions.",
        ["design storm", "standard", "100-year", "town"],
        ["chk_design_storm_consistent"], ["find_storm_conflict"],
    ),
    _chunk(
        "chunk_muni_003", "doc_municipal_checklist", 2, "O&M Requirement", 2,
        "A recorded maintenance agreement identifying the responsible party is "
        "required for shared stormwater facilities.",
        ["operation and maintenance", "agreement", "responsible party"],
        ["chk_oem_owner"], ["find_oem_owner"],
    ),
    _chunk(
        "chunk_muni_004", "doc_municipal_checklist", 2, "Infiltration", 3,
        "Infiltration practices require field infiltration testing and documented "
        "separation to seasonal high groundwater.",
        ["infiltration testing", "groundwater separation", "requirement"],
        ["chk_infiltration_testing", "chk_groundwater_separation"],
        ["find_infiltration_missing", "find_gw_separation"],
    ),
]


def _source(
    finding_source_id: str,
    finding_id: str,
    document_id: str,
    chunk_id: str,
    page: int | None,
    excerpt: str,
    role: str,
    confidence: float,
) -> dict:
    return {
        "finding_source_id": finding_source_id,
        "finding_id": finding_id,
        "document_id": document_id,
        "chunk_id": chunk_id,
        "page_number": page,
        "excerpt": excerpt,
        "evidence_role": role,
        "confidence": confidence,
    }


FINDING_SOURCES: list[dict] = [
    _source(
        "fs_storm_01", "find_storm_conflict", "doc_stormwater_report",
        "chunk_swm_001", 2,
        "Hydrologic analysis uses the 25-year, 24-hour design storm for "
        "peak-flow attenuation sizing.",
        "shows_conflict", 0.90,
    ),
    _source(
        "fs_storm_02", "find_storm_conflict", "doc_municipal_checklist",
        "chunk_muni_002", 1,
        "The town standard requires analysis of the 2, 10, and 100-year design "
        "storms for post-development conditions.",
        "shows_conflict", 0.92,
    ),
    _source(
        "fs_infil_01", "find_infiltration_missing", "doc_soils_report",
        "chunk_soil_004", 5,
        "Field infiltration testing was not performed as part of this "
        "geotechnical scope.",
        "shows_missing_evidence", 0.88,
    ),
    _source(
        "fs_infil_02", "find_infiltration_missing", "doc_stormwater_report",
        "chunk_swm_003", 4,
        "Infiltration testing is noted as to be provided under separate cover.",
        "shows_missing_evidence", 0.80,
    ),
    _source(
        "fs_infil_03", "find_infiltration_missing", "doc_municipal_checklist",
        "chunk_muni_004", 2,
        "Infiltration practices require field infiltration testing.",
        "context_only", 0.70,
    ),
    _source(
        "fs_gw_01", "find_gw_separation", "doc_soils_report",
        "chunk_soil_003", 4,
        "Seasonal high groundwater was observed within about 2.5 to 3.5 ft of "
        "existing grade in the lower meadow.",
        "shows_conflict", 0.85,
    ),
    _source(
        "fs_gw_02", "find_gw_separation", "doc_stormwater_report",
        "chunk_swm_005", 5,
        "The report does not include a separation analysis between the "
        "infiltration basin bottom and seasonal high groundwater.",
        "shows_missing_evidence", 0.82,
    ),
    _source(
        "fs_down_01", "find_downstream_capacity", "doc_hydraulic_calcs",
        "chunk_hyd_003", 2,
        "Downstream culvert capacity at Quarry Road is not evaluated in this "
        "submission.",
        "shows_missing_evidence", 0.86,
    ),
    _source(
        "fs_down_02", "find_downstream_capacity", "doc_existing_conditions",
        "chunk_exist_002", 1,
        "Existing runoff discharges through an existing 36-inch culvert under "
        "Quarry Road.",
        "context_only", 0.70,
    ),
    _source(
        "fs_oem_01", "find_oem_owner", "doc_oem_plan",
        "chunk_oem_003", 2,
        "The plan references HOA maintenance but does not include a recorded "
        "agreement binding the homeowners association to the work.",
        "shows_missing_evidence", 0.84,
    ),
    _source(
        "fs_oem_02", "find_oem_owner", "doc_site_narrative",
        "chunk_site_003", 2,
        "Long-term maintenance is intended to be handled by the future "
        "homeowners association.",
        "context_only", 0.66,
    ),
    _source(
        "fs_oem_03", "find_oem_owner", "doc_municipal_checklist",
        "chunk_muni_003", 2,
        "A recorded maintenance agreement identifying the responsible party is "
        "required for shared stormwater facilities.",
        "requires_reviewer_confirmation", 0.70,
    ),
    _source(
        "fs_escp_01", "find_escp_phasing", "doc_escp",
        "chunk_escp_004", 2,
        "The plan does not tie control installation to the two construction "
        "phases.",
        "shows_missing_evidence", 0.83,
    ),
    _source(
        "fs_escp_02", "find_escp_phasing", "doc_phasing_plan",
        "chunk_phase_001", 1,
        "Construction is proposed in two phases: upland lots first, then the "
        "lower meadow lots and basins.",
        "context_only", 0.68,
    ),
    _source(
        "fs_insp_01", "find_inspection_open", "doc_inspection_notes",
        "chunk_insp_002", 1,
        "Sediment accumulation was observed at the basin outlet during the "
        "inspection.",
        "supports_finding", 0.80,
    ),
    _source(
        "fs_insp_02", "find_inspection_open", "doc_inspection_notes",
        "chunk_insp_003", 2,
        "No corrective action entry or closeout was recorded for the observed "
        "sediment at the outlet.",
        "shows_missing_evidence", 0.85,
    ),
    _source(
        "fs_rfi_01", "find_rfi_open", "doc_rfi_log",
        "chunk_rfi_002", 1,
        "RFI-07 asks whether storm drain pipe should be reinforced concrete or "
        "HDPE.",
        "supports_finding", 0.80,
    ),
    _source(
        "fs_rfi_02", "find_rfi_open", "doc_rfi_log",
        "chunk_rfi_003", 1,
        "RFI-07 is shown as open with no recorded response.",
        "shows_missing_evidence", 0.86,
    ),
    _source(
        "fs_basin_01", "find_basin_naming", "doc_grading_drainage",
        "chunk_grade_002", 2,
        "Pond A is the wet detention basin in the southeast low area.",
        "shows_conflict", 0.90,
    ),
    _source(
        "fs_basin_02", "find_basin_naming", "doc_stormwater_report",
        "chunk_swm_002", 3,
        "Basin 1, the wet detention basin, is sized to attenuate post-development "
        "peak flows.",
        "shows_conflict", 0.90,
    ),
    _source(
        "fs_sheet_01", "find_missing_sheet", "doc_site_narrative",
        "chunk_site_004", 3,
        "Grading revisions are shown on revised sheet C-3.1, noted as included "
        "under separate cover.",
        "shows_missing_evidence", 0.80,
    ),
]


RETRIEVAL_QUERIES: list[dict] = [
    {
        "retrieval_query_id": "rq_infiltration_testing",
        "project_id": PROJECT_ID,
        "query_text": "infiltration testing",
        "related_checklist_item_id": "chk_infiltration_testing",
        "result_count": 4,
    },
    {
        "retrieval_query_id": "rq_downstream_culvert",
        "project_id": PROJECT_ID,
        "query_text": "downstream culvert capacity",
        "related_checklist_item_id": "chk_downstream_capacity",
        "result_count": 2,
    },
    {
        "retrieval_query_id": "rq_operation_maintenance",
        "project_id": PROJECT_ID,
        "query_text": "operation and maintenance responsibility",
        "related_checklist_item_id": "chk_oem_owner",
        "result_count": 4,
    },
    {
        "retrieval_query_id": "rq_seasonal_high_groundwater",
        "project_id": PROJECT_ID,
        "query_text": "seasonal high groundwater",
        "related_checklist_item_id": "chk_groundwater_separation",
        "result_count": 2,
    },
    {
        "retrieval_query_id": "rq_design_storm",
        "project_id": PROJECT_ID,
        "query_text": "design storm",
        "related_checklist_item_id": "chk_design_storm_consistent",
        "result_count": 3,
    },
]


def evidence_is_loaded(db: Session) -> bool:
    """Return True if document chunks are already present."""

    return db.query(models.DocumentChunk).first() is not None


def seed_evidence(db: Session, *, force: bool = False) -> None:
    """Load seeded chunks, finding sources, and retrieval queries.

    Idempotent: skips if evidence is already present unless force is True.
    """

    if evidence_is_loaded(db):
        if not force:
            return
        for model in (
            models.RetrievalQuery,
            models.FindingSource,
            models.DocumentChunk,
        ):
            db.query(model).delete()
        db.commit()

    db.add_all(models.DocumentChunk(**chunk) for chunk in CHUNKS)
    db.add_all(models.FindingSource(**source) for source in FINDING_SOURCES)
    db.add_all(models.RetrievalQuery(**query) for query in RETRIEVAL_QUERIES)
    db.commit()
