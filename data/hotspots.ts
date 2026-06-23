// Static hotspot overlay data for the homepage hero map.
// Source of truth: docs/HOMEPAGE_HOTSPOT_PLAN.md
//
// The hero image (public/development.png) is treated as a product feature: a
// future interactive development map. These records drive the Phase 1 static
// overlay markers and tooltips/side panel.
//
// NOTE: position.xPercent / yPercent are visual estimates measured from the
// top-left of the image. Final coordinates should be adjusted after viewing
// the deployed page against the actual development.png artwork.

export type HotspotCategory =
  | "stormwater"
  | "wetland"
  | "roadway"
  | "erosion_control"
  | "utility"
  | "lots"
  | "risk";

export type Hotspot = {
  id: string;
  name: string;
  category: HotspotCategory;
  shortDescription: string;
  civilPurpose: string;
  relatedChecklistItems: string[];
  relatedPlantedIssues: string[];
  futureDrilldown: string;
  position: {
    xPercent: number;
    yPercent: number;
  };
};

export const hotspots: Hotspot[] = [
  {
    id: "hotspot_wet_detention_basin",
    name: "Wet detention basin (Basin 1)",
    category: "stormwater",
    shortDescription:
      "Gray-infrastructure detention basin attenuating peak flow before the culvert outfall.",
    civilPurpose:
      "Peak-flow attenuation and water-quality settling prior to discharge toward the Quarry Road culvert.",
    relatedChecklistItems: [
      "chk_bmp_identified",
      "chk_outfall_identified",
      "chk_reference_consistency",
    ],
    relatedPlantedIssues: ["I-9"],
    futureDrilldown:
      "Drill-down to basin sizing evidence, outfall details, and the Pond A / Basin 1 naming-conflict finding.",
    position: { xPercent: 68, yPercent: 72 },
  },
  {
    id: "hotspot_infiltration_meadow_basin",
    name: "Infiltration basin (Basin 2)",
    category: "stormwater",
    shortDescription:
      "Green-infrastructure infiltration basin in the meadow for volume reduction and recharge.",
    civilPurpose:
      "Runoff volume reduction and groundwater recharge — feasibility depends on infiltration testing and groundwater separation.",
    relatedChecklistItems: [
      "chk_infiltration_testing",
      "chk_groundwater_separation",
      "chk_soil_groundwater_doc",
    ],
    relatedPlantedIssues: ["I-2", "I-3"],
    futureDrilldown:
      "Drill-down to infiltration testing evidence (missing) and the seasonal high groundwater separation discussion.",
    position: { xPercent: 52, yPercent: 60 },
  },
  {
    id: "hotspot_wetland_stream_corridor",
    name: "Wetland buffer & Brook Run corridor",
    category: "wetland",
    shortDescription:
      "Delineated wetland and intermittent stream with a 100-ft town buffer along the southeast boundary.",
    civilPurpose:
      "Protected resource area; proposed outfalls and grading near the buffer require Conservation Commission coordination.",
    relatedChecklistItems: ["chk_outfall_identified", "chk_downstream_capacity"],
    relatedPlantedIssues: [],
    futureDrilldown:
      "Drill-down to buffer encroachment review, outfall locations, and receiving-water context.",
    position: { xPercent: 80, yPercent: 85 },
  },
  {
    id: "hotspot_quarry_road_culvert",
    name: "Quarry Road culvert",
    category: "stormwater",
    shortDescription:
      "Existing 36-inch culvert and downstream discharge point with reported road-edge ponding.",
    civilPurpose:
      "Downstream conveyance structure; post-development flows must not worsen downstream conditions.",
    relatedChecklistItems: ["chk_downstream_capacity"],
    relatedPlantedIssues: ["I-4"],
    futureDrilldown:
      "Drill-down to the downstream capacity analysis (missing) and the downstream ponding concern.",
    position: { xPercent: 90, yPercent: 78 },
  },
  {
    id: "hotspot_construction_entrance",
    name: "Construction entrance",
    category: "erosion_control",
    shortDescription:
      "Stabilized construction entrance off Quarry Road to control tracked sediment.",
    civilPurpose:
      "Construction-phase access point and sediment-tracking control at the site entrance.",
    relatedChecklistItems: ["chk_erosion_controls", "chk_escp_phasing"],
    relatedPlantedIssues: [],
    futureDrilldown:
      "Drill-down to the erosion & sediment control plan and construction sequencing.",
    position: { xPercent: 84, yPercent: 64 },
  },
  {
    id: "hotspot_erosion_control_perimeter",
    name: "Erosion control perimeter",
    category: "erosion_control",
    shortDescription:
      "Silt fence and perimeter controls along the downhill limits of disturbance near the buffer.",
    civilPurpose:
      "Perimeter sediment control during phased clearing on slopes draining toward Brook Run.",
    relatedChecklistItems: ["chk_erosion_controls", "chk_escp_phasing"],
    relatedPlantedIssues: ["I-6"],
    futureDrilldown:
      "Drill-down to the E&SC phasing finding and stabilization timing.",
    position: { xPercent: 40, yPercent: 78 },
  },
  {
    id: "hotspot_loop_road_lots",
    name: "Loop road subdivision lots",
    category: "lots",
    shortDescription:
      "Upland lots served by the loop road, with rooftop and driveway impervious cover.",
    civilPurpose:
      "Primary residential development area contributing new impervious runoff to the storm drain network.",
    relatedChecklistItems: ["chk_drainage_areas", "chk_runoff_calcs"],
    relatedPlantedIssues: [],
    futureDrilldown:
      "Drill-down to drainage-area mapping and runoff calculations for proposed conditions.",
    position: { xPercent: 35, yPercent: 38 },
  },
  {
    id: "hotspot_culdesac_lower_lots",
    name: "Cul-de-sac lower lots",
    category: "lots",
    shortDescription:
      "Lower lots on Meadow Court near the buffer and shallow groundwater area.",
    civilPurpose:
      "Lower-elevation lots sensitive to groundwater and proximity to the wetland buffer.",
    relatedChecklistItems: ["chk_groundwater_separation", "chk_drainage_areas"],
    relatedPlantedIssues: ["I-3"],
    futureDrilldown:
      "Drill-down to groundwater separation context and lower-lot grading.",
    position: { xPercent: 62, yPercent: 50 },
  },
  {
    id: "hotspot_utility_pump_station",
    name: "Utility / pump station area",
    category: "utility",
    shortDescription:
      "Water main, gravity sewer, and a sanitary pump station serving the low lots.",
    civilPurpose:
      "Utility extensions and pump station; storm-drain and buffer crossings are future coordination points.",
    relatedChecklistItems: ["chk_rfi_closure"],
    relatedPlantedIssues: ["I-8"],
    futureDrilldown:
      "Drill-down to the open pipe-material RFI and utility / storm crossing coordination.",
    position: { xPercent: 58, yPercent: 30 },
  },
  {
    id: "hotspot_planted_review_issues",
    name: "Planted review issue locations",
    category: "risk",
    shortDescription:
      "Overlay summarizing where the ten planted review issues surface across the package.",
    civilPurpose:
      "Demonstration overlay linking map locations to the expected review-support findings.",
    relatedChecklistItems: [
      "chk_design_storm_consistent",
      "chk_infiltration_testing",
      "chk_downstream_capacity",
      "chk_oem_owner",
      "chk_inspection_closeout",
      "chk_referenced_sheets_present",
    ],
    relatedPlantedIssues: [
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
    futureDrilldown:
      "Drill-down to the full findings list with map-linked evidence and human review status.",
    position: { xPercent: 22, yPercent: 60 },
  },
];
