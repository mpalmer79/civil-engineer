"""Seeded site map hotspots for the Brookside Meadows fixture.

Review-support annotations placed over the synthetic site map using
percentage coordinates. This is seeded demonstration data, not extracted
plan geometry.
"""

from __future__ import annotations

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
