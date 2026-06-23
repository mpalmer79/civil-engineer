// Seeded synthetic document package for Brookside Meadows.
// Source of truth: docs/SEED_DATA_PLAN.md §2.
// Phase 1 uses seeded synthetic document records. Later phases will add
// ingestion, chunking, embeddings, and retrieval.

export type DocumentStatus =
  | "present"
  | "partial"
  | "missing"
  | "referenced_not_included"
  | "not_yet_submitted";

export type ReviewDocument = {
  documentId: string;
  fileName: string;
  documentType: string;
  status: DocumentStatus;
  purpose: string;
  expectedKeyInformation: string;
  knownIssue: string | null;
};

export const documents: ReviewDocument[] = [
  {
    documentId: "doc_site_narrative",
    fileName: "site-plan-narrative.pdf",
    documentType: "site_plan_narrative",
    status: "present",
    purpose: "Describe the project and stormwater approach",
    expectedKeyInformation: "Project scope, phasing intent, BMP strategy",
    knownIssue: "References revised sheet C-3.1 (not included)",
  },
  {
    documentId: "doc_existing_conditions",
    fileName: "existing-conditions-plan.pdf",
    documentType: "existing_conditions_plan",
    status: "present",
    purpose: "Show pre-development site",
    expectedKeyInformation:
      "Topography, wood line, meadow, stream, wetland, culvert",
    knownIssue: null,
  },
  {
    documentId: "doc_layout_plan",
    fileName: "layout-plan.pdf",
    documentType: "layout_plan",
    status: "present",
    purpose: "Show lots and roads",
    expectedKeyInformation:
      "47 lots, Brookside Drive, loop, Meadow Court cul-de-sac, sidewalks",
    knownIssue: null,
  },
  {
    documentId: "doc_grading_drainage",
    fileName: "grading-and-drainage-plan.pdf",
    documentType: "grading_drainage_plan",
    status: "present",
    purpose: "Show grading and storm system",
    expectedKeyInformation: "Grading, storm drain, basin locations",
    knownIssue: 'Labels basin "Pond A" (conflicts with report\'s "Basin 1")',
  },
  {
    documentId: "doc_utility_plan",
    fileName: "utility-plan.pdf",
    documentType: "utility_plan",
    status: "present",
    purpose: "Show utilities",
    expectedKeyInformation:
      "Water main, gravity sewer, pump station, dry utilities",
    knownIssue: null,
  },
  {
    documentId: "doc_stormwater_report",
    fileName: "stormwater-management-report.pdf",
    documentType: "stormwater_management_report",
    status: "present",
    purpose: "Describe permanent stormwater controls",
    expectedKeyInformation: "BMP selection, treatment train, basin sizing",
    knownIssue:
      'Uses 25-year design storm; calls basin "Basin 1"; does not address groundwater separation',
  },
  {
    documentId: "doc_hydrology_calcs",
    fileName: "hydrology-calculations.pdf",
    documentType: "hydrology_calculations",
    status: "present",
    purpose: "Runoff / peak-flow calculations",
    expectedKeyInformation: "CN, Tc, peak flows existing vs. proposed",
    knownIssue: null,
  },
  {
    documentId: "doc_hydraulic_calcs",
    fileName: "hydraulic-calculations.pdf",
    documentType: "hydraulic_calculations",
    status: "partial",
    purpose: "Pipe / outlet sizing",
    expectedKeyInformation: "Pipe capacity, outlet structure sizing",
    knownIssue: "No downstream culvert capacity analysis",
  },
  {
    documentId: "doc_soils_report",
    fileName: "soils-geotechnical-report.pdf",
    documentType: "soil_report",
    status: "present",
    purpose: "Subsurface conditions",
    expectedKeyInformation: "Soil groups, borings, seasonal high groundwater",
    knownIssue:
      "Notes seasonal high groundwater (separation never reconciled in stormwater report)",
  },
  {
    documentId: "doc_infiltration_logs",
    fileName: "infiltration-testing-logs.pdf",
    documentType: "infiltration_testing_documentation",
    status: "missing",
    purpose: "Support the infiltration basin",
    expectedKeyInformation:
      "Test locations, rates, method, date, depth to groundwater",
    knownIssue: "Missing / incomplete for a proposed infiltration practice",
  },
  {
    documentId: "doc_escp",
    fileName: "erosion-sediment-control-plan.pdf",
    documentType: "erosion_control_plan",
    status: "present",
    purpose: "Construction-phase controls",
    expectedKeyInformation:
      "Silt fence, inlet protection, construction entrance, stabilization",
    knownIssue: "Not clearly tied to construction phasing",
  },
  {
    documentId: "doc_swppp",
    fileName: "swppp.pdf",
    documentType: "swppp",
    status: "present",
    purpose: "Construction stormwater pollution prevention",
    expectedKeyInformation:
      "Controls, inspection commitments, corrective-action procedure",
    knownIssue: "Template-level; light on site-specific detail",
  },
  {
    documentId: "doc_oem_plan",
    fileName: "operation-maintenance-plan.pdf",
    documentType: "o_and_m_plan",
    status: "present",
    purpose: "Long-term BMP maintenance",
    expectedKeyInformation: "Tasks, frequency, access, responsible owner",
    knownIssue:
      'References "HOA maintenance" but HOA responsibility not formally documented',
  },
  {
    documentId: "doc_phasing_plan",
    fileName: "construction-phasing-plan.pdf",
    documentType: "construction_phasing_plan",
    status: "present",
    purpose: "Construction sequence",
    expectedKeyInformation: "Two phases: upland then lower meadow",
    knownIssue: "Inconsistent with the E&SC plan's sequencing",
  },
  {
    documentId: "doc_inspection_notes",
    fileName: "inspection-notes.pdf",
    documentType: "inspection_notes",
    status: "present",
    purpose: "Field observations",
    expectedKeyInformation: "Date, inspector, observations",
    knownIssue: "Flags sediment at basin outlet; no corrective action logged",
  },
  {
    documentId: "doc_rfi_log",
    fileName: "rfi-log.pdf",
    documentType: "rfi_log",
    status: "present",
    purpose: "Track questions",
    expectedKeyInformation: "RFI number, question, status",
    knownIssue: "RFI asks pipe material; no response recorded",
  },
  {
    documentId: "doc_municipal_checklist",
    fileName: "town-stormwater-checklist.pdf",
    documentType: "municipal_checklist",
    status: "present",
    purpose: "Town submission requirements",
    expectedKeyInformation:
      "Required reports, design-storm standard, O&M requirement",
    knownIssue: "Expects a different design storm than the report's 25-year",
  },
  {
    documentId: "doc_comment_response",
    fileName: "comment-response-letter.pdf",
    documentType: "comment_response_letter",
    status: "not_yet_submitted",
    purpose: "Respond to review comments",
    expectedKeyInformation: "Responses to each comment",
    knownIssue: "First submission — none yet",
  },
  {
    documentId: "doc_revised_c31",
    fileName: "grading-sheet-C-3.1-REV.pdf",
    documentType: "grading_drainage_plan",
    status: "referenced_not_included",
    purpose: "Revised grading sheet",
    expectedKeyInformation: "Revised grading per narrative",
    knownIssue: "Referenced but absent from the package",
  },
];
