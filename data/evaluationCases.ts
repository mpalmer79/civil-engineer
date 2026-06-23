// Seeded evaluation cases for Brookside Meadows.
// Source of truth: docs/SEED_DATA_PLAN.md §5.
//
// Phase 1 displays seeded evaluation outcomes. Later phases will run evaluation
// cases against generated findings. The metric values below are mock but
// plausible for a static prototype.

export type EvaluationCase = {
  evalCaseId: string;
  name: string;
  inputDocuments: string[];
  expectedFindingId: string | null;
  expectedRiskLevel: "low" | "medium" | "high";
  primaryMetric: string;
  expectedFindingsDetected: string; // e.g. "1 / 1"
  sourceCitationAccuracy: number; // 0..1
  falsePositives: number;
  falseNegatives: number;
  unsupportedClaims: number;
  prohibitedWordingCount: number;
  humanReviewRequired: number;
  passed: boolean;
};

export const evaluationCases: EvaluationCase[] = [
  {
    evalCaseId: "eval_infiltration_missing",
    name: "Missing infiltration testing",
    inputDocuments: ["doc_stormwater_report", "doc_soils_report"],
    expectedFindingId: "find_infiltration_missing",
    expectedRiskLevel: "high",
    primaryMetric: "recall",
    expectedFindingsDetected: "1 / 1",
    sourceCitationAccuracy: 0.95,
    falsePositives: 0,
    falseNegatives: 0,
    unsupportedClaims: 0,
    prohibitedWordingCount: 0,
    humanReviewRequired: 1,
    passed: true,
  },
  {
    evalCaseId: "eval_storm_conflict",
    name: "Conflicting storm event assumption",
    inputDocuments: [
      "doc_stormwater_report",
      "doc_hydrology_calcs",
      "doc_municipal_checklist",
    ],
    expectedFindingId: "find_storm_conflict",
    expectedRiskLevel: "high",
    primaryMetric: "recall",
    expectedFindingsDetected: "1 / 1",
    sourceCitationAccuracy: 0.92,
    falsePositives: 0,
    falseNegatives: 0,
    unsupportedClaims: 0,
    prohibitedWordingCount: 0,
    humanReviewRequired: 1,
    passed: true,
  },
  {
    evalCaseId: "eval_oem_owner",
    name: "Missing O&M responsibility",
    inputDocuments: ["doc_oem_plan", "doc_site_narrative"],
    expectedFindingId: "find_oem_owner",
    expectedRiskLevel: "high",
    primaryMetric: "recall",
    expectedFindingsDetected: "1 / 1",
    sourceCitationAccuracy: 0.9,
    falsePositives: 0,
    falseNegatives: 0,
    unsupportedClaims: 0,
    prohibitedWordingCount: 0,
    humanReviewRequired: 1,
    passed: true,
  },
  {
    evalCaseId: "eval_rfi_open",
    name: "Unresolved RFI",
    inputDocuments: ["doc_rfi_log"],
    expectedFindingId: "find_rfi_open",
    expectedRiskLevel: "medium",
    primaryMetric: "recall",
    expectedFindingsDetected: "1 / 1",
    sourceCitationAccuracy: 0.93,
    falsePositives: 0,
    falseNegatives: 0,
    unsupportedClaims: 0,
    prohibitedWordingCount: 0,
    humanReviewRequired: 1,
    passed: true,
  },
  {
    evalCaseId: "eval_downstream_capacity",
    name: "Missing downstream capacity discussion",
    inputDocuments: [
      "doc_hydraulic_calcs",
      "doc_stormwater_report",
      "doc_existing_conditions",
    ],
    expectedFindingId: "find_downstream_capacity",
    expectedRiskLevel: "high",
    primaryMetric: "recall",
    expectedFindingsDetected: "1 / 1",
    sourceCitationAccuracy: 0.88,
    falsePositives: 0,
    falseNegatives: 0,
    unsupportedClaims: 0,
    prohibitedWordingCount: 0,
    humanReviewRequired: 1,
    passed: true,
  },
  {
    evalCaseId: "eval_inspection_open",
    name: "Inspection note without corrective action",
    inputDocuments: ["doc_inspection_notes"],
    expectedFindingId: "find_inspection_open",
    expectedRiskLevel: "high",
    primaryMetric: "recall",
    expectedFindingsDetected: "1 / 1",
    sourceCitationAccuracy: 0.94,
    falsePositives: 0,
    falseNegatives: 0,
    unsupportedClaims: 0,
    prohibitedWordingCount: 0,
    humanReviewRequired: 1,
    passed: true,
  },
  {
    evalCaseId: "eval_basin_naming",
    name: "Conflicting basin names",
    inputDocuments: ["doc_grading_drainage", "doc_stormwater_report"],
    expectedFindingId: "find_basin_naming",
    expectedRiskLevel: "medium",
    primaryMetric: "source_citation_accuracy",
    expectedFindingsDetected: "1 / 1",
    sourceCitationAccuracy: 0.97,
    falsePositives: 0,
    falseNegatives: 0,
    unsupportedClaims: 0,
    prohibitedWordingCount: 0,
    humanReviewRequired: 1,
    passed: true,
  },
  {
    evalCaseId: "eval_clean_control",
    name: "Clean control, no false positives",
    inputDocuments: [
      "doc_existing_conditions",
      "doc_layout_plan",
      "doc_hydrology_calcs",
    ],
    expectedFindingId: null,
    expectedRiskLevel: "low",
    primaryMetric: "no_false_positive",
    expectedFindingsDetected: "0 / 0",
    sourceCitationAccuracy: 1.0,
    falsePositives: 0,
    falseNegatives: 0,
    unsupportedClaims: 0,
    prohibitedWordingCount: 0,
    humanReviewRequired: 0,
    passed: true,
  },
];

// Aggregate values for the evaluation dashboard summary cards.
export const evaluationSummary = {
  totalCases: evaluationCases.length,
  casesPassed: evaluationCases.filter((c) => c.passed).length,
  expectedFindingsDetected: "7 / 7",
  averageSourceCitationAccuracy: 0.93,
  totalFalsePositives: evaluationCases.reduce((n, c) => n + c.falsePositives, 0),
  totalFalseNegatives: evaluationCases.reduce((n, c) => n + c.falseNegatives, 0),
  totalUnsupportedClaims: evaluationCases.reduce(
    (n, c) => n + c.unsupportedClaims,
    0,
  ),
  prohibitedWordingCount: evaluationCases.reduce(
    (n, c) => n + c.prohibitedWordingCount,
    0,
  ),
  humanReviewRequired: evaluationCases.reduce(
    (n, c) => n + c.humanReviewRequired,
    0,
  ),
};
