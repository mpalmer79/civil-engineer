// Seeded expected review-support findings for Brookside Meadows.
// Source of truth: docs/SEED_DATA_PLAN.md §4 and the planted issues in
// docs/BROOKSIDE_MEADOWS_PROJECT_STORY.md §7.
//
// These are framed as EXPECTED findings that need reviewer confirmation. They
// are review-support issues, not final engineering conclusions. No finding is
// final without a recorded human review action.

import type { ChecklistStatus, ChecklistRisk } from "./checklist";

export type HumanReviewState =
  | "pending"
  | "accepted"
  | "edited"
  | "rejected"
  | "escalated";

export type Finding = {
  findingId: string;
  plantedIssue: string;
  title: string;
  category: string;
  riskLevel: ChecklistRisk;
  expectedStatus: ChecklistStatus;
  checklistItemId: string;
  evidenceToFind: string;
  whyItMatters: string;
  recommendedHumanAction: string;
  humanReviewState: HumanReviewState;
};

export const findings: Finding[] = [
  {
    findingId: "find_storm_conflict",
    plantedIssue: "I-1",
    title: "Design-storm assumption conflicts with town standard",
    category: "Design storm",
    riskLevel: "high",
    expectedStatus: "conflicting",
    checklistItemId: "chk_design_storm_consistent",
    evidenceToFind:
      "Report states a 25-year storm; the town checklist expects a different event",
    whyItMatters:
      "Inconsistent design-storm criteria can invalidate review conclusions about peak flow and basin sizing.",
    recommendedHumanAction:
      "Confirm the applicable town standard and request a correction or clarification from the applicant.",
    humanReviewState: "pending",
  },
  {
    findingId: "find_infiltration_missing",
    plantedIssue: "I-2",
    title: "Infiltration testing not found for proposed infiltration basin",
    category: "Infiltration",
    riskLevel: "high",
    expectedStatus: "missing",
    checklistItemId: "chk_infiltration_testing",
    evidenceToFind:
      "An infiltration basin is proposed, but no field infiltration testing logs are in the package",
    whyItMatters:
      "Infiltration BMPs depend on site-specific testing; without it, feasibility and sizing cannot be confirmed.",
    recommendedHumanAction:
      "Request field infiltration testing documentation or a design revision.",
    humanReviewState: "pending",
  },
  {
    findingId: "find_gw_separation",
    plantedIssue: "I-3",
    title: "Groundwater separation for infiltration not addressed",
    category: "Infiltration",
    riskLevel: "high",
    expectedStatus: "unclear",
    checklistItemId: "chk_groundwater_separation",
    evidenceToFind:
      "Soils report notes seasonal high groundwater; the stormwater report omits a separation discussion",
    whyItMatters:
      "Inadequate separation to seasonal high groundwater undermines infiltration feasibility and performance.",
    recommendedHumanAction:
      "Request a separation analysis that references the documented seasonal high groundwater depth.",
    humanReviewState: "pending",
  },
  {
    findingId: "find_downstream_capacity",
    plantedIssue: "I-4",
    title: "Downstream culvert capacity not analyzed",
    category: "Downstream",
    riskLevel: "high",
    expectedStatus: "missing",
    checklistItemId: "chk_downstream_capacity",
    evidenceToFind:
      "The Quarry Road culvert is referenced, but no downstream capacity analysis is included",
    whyItMatters:
      "Post-development peak flows could worsen reported downstream road-edge ponding if capacity is not evaluated.",
    recommendedHumanAction:
      "Request a downstream conveyance / culvert capacity analysis.",
    humanReviewState: "pending",
  },
  {
    findingId: "find_oem_owner",
    plantedIssue: "I-5",
    title: "Maintenance owner not clearly bound",
    category: "O&M",
    riskLevel: "high",
    expectedStatus: "unclear",
    checklistItemId: "chk_oem_owner",
    evidenceToFind:
      'The O&M plan cites "HOA maintenance" without documented, binding responsibility',
    whyItMatters:
      "Unclear long-term maintenance responsibility creates a failure risk for shared stormwater facilities.",
    recommendedHumanAction:
      "Request formal documentation of HOA maintenance responsibility and access.",
    humanReviewState: "pending",
  },
  {
    findingId: "find_escp_phasing",
    plantedIssue: "I-6",
    title: "E&SC sequencing not tied to phasing",
    category: "Erosion",
    riskLevel: "medium",
    expectedStatus: "conflicting",
    checklistItemId: "chk_escp_phasing",
    evidenceToFind:
      "The erosion & sediment control plan lacks phased sequencing consistent with the phasing plan",
    whyItMatters:
      "Phased clearing on slopes draining to a stream raises sediment-control sequencing risk.",
    recommendedHumanAction:
      "Request phased E&SC sequencing aligned with the construction phasing plan.",
    humanReviewState: "pending",
  },
  {
    findingId: "find_inspection_open",
    plantedIssue: "I-7",
    title: "Inspection deficiency without corrective action",
    category: "Inspection",
    riskLevel: "high",
    expectedStatus: "unresolved",
    checklistItemId: "chk_inspection_closeout",
    evidenceToFind:
      "An inspection note flags sediment at the basin outlet, but no corrective action is logged",
    whyItMatters:
      "A field deficiency with no recorded closeout may remain unresolved.",
    recommendedHumanAction:
      "Request corrective-action evidence or closeout documentation.",
    humanReviewState: "pending",
  },
  {
    findingId: "find_rfi_open",
    plantedIssue: "I-8",
    title: "Open RFI on pipe material with no response",
    category: "RFI",
    riskLevel: "medium",
    expectedStatus: "conflicting",
    checklistItemId: "chk_rfi_closure",
    evidenceToFind:
      "An RFI asks about pipe material, but no response is recorded in the log",
    whyItMatters:
      "An open RFI can signal an unresolved design detail that affects the storm drain network.",
    recommendedHumanAction:
      "Hold the related item pending a response; confirm the proposed pipe material.",
    humanReviewState: "pending",
  },
  {
    findingId: "find_basin_naming",
    plantedIssue: "I-9",
    title: "Inconsistent basin naming across documents",
    category: "Consistency",
    riskLevel: "medium",
    expectedStatus: "conflicting",
    checklistItemId: "chk_reference_consistency",
    evidenceToFind:
      'The grading plan labels the basin "Pond A" while the stormwater report calls it "Basin 1"',
    whyItMatters:
      "Conflicting labels across documents create review confusion and traceability gaps.",
    recommendedHumanAction:
      "Request consistent basin naming across the plan set and report.",
    humanReviewState: "pending",
  },
  {
    findingId: "find_missing_sheet",
    plantedIssue: "I-10",
    title: "Referenced revised grading sheet C-3.1 not included",
    category: "Completeness",
    riskLevel: "medium",
    expectedStatus: "missing",
    checklistItemId: "chk_referenced_sheets_present",
    evidenceToFind:
      "The narrative cites a revised sheet C-3.1 that is absent from the package",
    whyItMatters:
      "A cited revision that is missing cannot be reviewed and may hide material changes.",
    recommendedHumanAction:
      "Request the missing revised grading sheet C-3.1.",
    humanReviewState: "pending",
  },
];
