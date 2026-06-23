// Seeded stormwater review checklist for Brookside Meadows.
// Source of truth: docs/SEED_DATA_PLAN.md §3.
// The checklist drives review structure. AI findings are tied to checklist
// items; the system does not rely on free-form AI judgment alone, and human
// review is required before any final action.

export type ChecklistStatus =
  | "supported"
  | "missing"
  | "conflicting"
  | "unclear"
  | "unresolved"
  | "not_applicable";

export type ChecklistRisk = "low" | "medium" | "high";

export type ChecklistItem = {
  checklistItemId: string;
  category: string;
  requirement: string;
  expectedEvidence: string;
  supportingDocuments: string;
  riskLevel: ChecklistRisk;
  appliesWhen: string;
  expectedStatus: ChecklistStatus;
  plantedIssue: string | null;
};

export const checklist: ChecklistItem[] = [
  {
    checklistItemId: "chk_pkg_completeness",
    category: "Completeness",
    requirement: "Package includes a stormwater / drainage report",
    expectedEvidence: "Stormwater or drainage report present",
    supportingDocuments: "stormwater_management_report",
    riskLevel: "high",
    appliesWhen: "always",
    expectedStatus: "supported",
    plantedIssue: null,
  },
  {
    checklistItemId: "chk_design_storm_stated",
    category: "Design storm",
    requirement: "Design-storm assumptions are stated",
    expectedEvidence: "Storm event, recurrence, rainfall depth",
    supportingDocuments: "stormwater_management_report, hydrology_calculations",
    riskLevel: "high",
    appliesWhen: "always",
    expectedStatus: "supported",
    plantedIssue: null,
  },
  {
    checklistItemId: "chk_design_storm_consistent",
    category: "Design storm",
    requirement:
      "Design storm matches the municipal standard and is consistent across documents",
    expectedEvidence: "Same event in report, calcs, and town checklist",
    supportingDocuments:
      "stormwater_management_report, hydrology_calculations, municipal_checklist",
    riskLevel: "high",
    appliesWhen: "always",
    expectedStatus: "conflicting",
    plantedIssue: "I-1",
  },
  {
    checklistItemId: "chk_drainage_areas",
    category: "Drainage areas",
    requirement: "Existing and proposed drainage areas identified",
    expectedEvidence: "Drainage area maps / tables",
    supportingDocuments:
      "existing_conditions_plan, grading_drainage_plan, hydrology_calculations",
    riskLevel: "medium",
    appliesWhen: "always",
    expectedStatus: "supported",
    plantedIssue: null,
  },
  {
    checklistItemId: "chk_runoff_calcs",
    category: "Runoff",
    requirement: "Runoff calcs for existing and proposed conditions",
    expectedEvidence: "Peak flow / volume calcs",
    supportingDocuments: "hydrology_calculations",
    riskLevel: "high",
    appliesWhen: "always",
    expectedStatus: "supported",
    plantedIssue: null,
  },
  {
    checklistItemId: "chk_bmp_identified",
    category: "BMP",
    requirement: "Proposed stormwater BMPs are identified",
    expectedEvidence: "BMP type, location, purpose",
    supportingDocuments: "stormwater_management_report, grading_drainage_plan",
    riskLevel: "medium",
    appliesWhen: "always",
    expectedStatus: "supported",
    plantedIssue: null,
  },
  {
    checklistItemId: "chk_infiltration_testing",
    category: "Infiltration",
    requirement: "If infiltration is proposed, infiltration testing is included",
    expectedEvidence: "Test locations, rates, method, date",
    supportingDocuments: "soil_report, infiltration_testing_documentation",
    riskLevel: "high",
    appliesWhen: "has_infiltration_practice",
    expectedStatus: "missing",
    plantedIssue: "I-2",
  },
  {
    checklistItemId: "chk_groundwater_separation",
    category: "Infiltration",
    requirement:
      "Separation to seasonal high groundwater is addressed for infiltration / bioretention",
    expectedEvidence: "Groundwater depth + separation discussion",
    supportingDocuments: "soil_report, stormwater_management_report",
    riskLevel: "high",
    appliesWhen: "has_infiltration_practice",
    expectedStatus: "unclear",
    plantedIssue: "I-3",
  },
  {
    checklistItemId: "chk_soil_groundwater_doc",
    category: "Soils",
    requirement: "Soil and groundwater conditions are documented",
    expectedEvidence: "Borings, soil groups, seasonal high groundwater",
    supportingDocuments: "soil_report",
    riskLevel: "high",
    appliesWhen: "always",
    expectedStatus: "supported",
    plantedIssue: null,
  },
  {
    checklistItemId: "chk_outfall_identified",
    category: "Outfall",
    requirement: "Outfalls / discharge points identified",
    expectedEvidence: "Outfall labels, receiving water, path",
    supportingDocuments: "grading_drainage_plan, stormwater_management_report",
    riskLevel: "medium",
    appliesWhen: "always",
    expectedStatus: "supported",
    plantedIssue: null,
  },
  {
    checklistItemId: "chk_downstream_capacity",
    category: "Downstream",
    requirement:
      "Downstream conveyance capacity is discussed where a downstream structure exists",
    expectedEvidence: "Downstream culvert capacity analysis",
    supportingDocuments: "hydraulic_calculations, stormwater_management_report",
    riskLevel: "high",
    appliesWhen: "has_downstream_structure",
    expectedStatus: "missing",
    plantedIssue: "I-4",
  },
  {
    checklistItemId: "chk_erosion_controls",
    category: "Erosion",
    requirement: "Erosion and sediment controls are shown",
    expectedEvidence:
      "Silt fence, inlet protection, construction entrance, stabilization",
    supportingDocuments: "erosion_control_plan, swppp",
    riskLevel: "medium",
    appliesWhen: "always",
    expectedStatus: "supported",
    plantedIssue: null,
  },
  {
    checklistItemId: "chk_escp_phasing",
    category: "Erosion",
    requirement: "E&SC measures are tied to construction phasing",
    expectedEvidence: "Phased control sequencing",
    supportingDocuments: "erosion_control_plan, construction_phasing_plan",
    riskLevel: "medium",
    appliesWhen: "always",
    expectedStatus: "conflicting",
    plantedIssue: "I-6",
  },
  {
    checklistItemId: "chk_oem_plan",
    category: "O&M",
    requirement: "Long-term operation & maintenance is addressed",
    expectedEvidence: "Tasks, schedule, access",
    supportingDocuments: "o_and_m_plan",
    riskLevel: "high",
    appliesWhen: "has_detention_basin OR has_infiltration_practice",
    expectedStatus: "supported",
    plantedIssue: null,
  },
  {
    checklistItemId: "chk_oem_owner",
    category: "O&M",
    requirement: "Responsible maintenance party is clearly identified",
    expectedEvidence:
      "Named owner (HOA / municipality / private) with binding responsibility",
    supportingDocuments: "o_and_m_plan, site_plan_narrative",
    riskLevel: "high",
    appliesWhen: "always",
    expectedStatus: "unclear",
    plantedIssue: "I-5",
  },
  {
    checklistItemId: "chk_rfi_closure",
    category: "RFI",
    requirement: "RFIs are resolved or clearly tracked",
    expectedEvidence: "RFI status and response",
    supportingDocuments: "rfi_log",
    riskLevel: "medium",
    appliesWhen: "always",
    expectedStatus: "conflicting",
    plantedIssue: "I-8",
  },
  {
    checklistItemId: "chk_inspection_closeout",
    category: "Inspection",
    requirement: "Inspection deficiencies have corrective-action closeout",
    expectedEvidence: "Corrective action status",
    supportingDocuments: "inspection_notes",
    riskLevel: "high",
    appliesWhen: "always",
    expectedStatus: "unresolved",
    plantedIssue: "I-7",
  },
  {
    checklistItemId: "chk_reference_consistency",
    category: "Consistency",
    requirement:
      "Basin / sheet / structure references are consistent across documents",
    expectedEvidence: "Matching labels across plan and report",
    supportingDocuments: "grading_drainage_plan, stormwater_management_report",
    riskLevel: "medium",
    appliesWhen: "always",
    expectedStatus: "conflicting",
    plantedIssue: "I-9",
  },
  {
    checklistItemId: "chk_referenced_sheets_present",
    category: "Completeness",
    requirement: "Referenced revised sheets are included in the package",
    expectedEvidence: "All cited sheets present",
    supportingDocuments: "site_plan_narrative, grading_drainage_plan",
    riskLevel: "medium",
    appliesWhen: "always",
    expectedStatus: "missing",
    plantedIssue: "I-10",
  },
];
