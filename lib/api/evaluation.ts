import {
  API_BASE_URL,
  PROJECT_ID,
  apiFetch,
  apiGetMapped,
  authHeaders,
  requireString,
  type ApiResult,
  type DemoDataSource,
} from "./client";
import {
  evaluationCases as staticEvaluationCases,
  evaluationSummary as staticEvaluationSummary,
  type EvaluationCase,
} from "@/data/evaluationCases";

type ApiEvaluationCase = {
  eval_case_id: string;
  name: string;
  input_documents: string[];
  expected_findings: string[];
  expected_risk_level: EvaluationCase["expectedRiskLevel"];
  evaluation_metric: string;
  seeded_result: {
    expected_findings_detected: string;
    source_citation_accuracy: number;
    false_positives: number;
    false_negatives: number;
    unsupported_claims: number;
    prohibited_wording_count: number;
    human_review_required: number;
    passed: boolean;
  };
};

function mapEvaluationCase(c: ApiEvaluationCase): EvaluationCase {
  const r = c.seeded_result;
  return {
    evalCaseId: c.eval_case_id,
    name: c.name,
    inputDocuments: c.input_documents,
    expectedFindingId: c.expected_findings[0] ?? null,
    expectedRiskLevel: c.expected_risk_level,
    primaryMetric: c.evaluation_metric,
    expectedFindingsDetected: r.expected_findings_detected,
    sourceCitationAccuracy: r.source_citation_accuracy,
    falsePositives: r.false_positives,
    falseNegatives: r.false_negatives,
    unsupportedClaims: r.unsupported_claims,
    prohibitedWordingCount: r.prohibited_wording_count,
    humanReviewRequired: r.human_review_required,
    passed: r.passed,
  };
}

export type EvaluationData = {
  cases: EvaluationCase[];
  summary: typeof staticEvaluationSummary;
  source: DemoDataSource;
};

export async function getEvaluationData(): Promise<EvaluationData> {
  const result = await apiFetch<ApiEvaluationCase[]>("/api/v1/evaluation-cases");
  // Explicit public-demo policy: when the demo backend is unreachable this
  // surface renders the repository fixture snapshot and says so.
  if (!result.ok) {
    return {
      cases: staticEvaluationCases,
      summary: staticEvaluationSummary,
      source: "demo_fixture",
    };
  }
  const cases = result.data.map(mapEvaluationCase);
  const summary = {
    totalCases: cases.length,
    casesPassed: cases.filter((c) => c.passed).length,
    expectedFindingsDetected: `${cases.filter(
      (c) => c.expectedFindingId !== null,
    ).length} / ${cases.filter((c) => c.expectedFindingId !== null).length}`,
    averageSourceCitationAccuracy:
      cases.reduce((n, c) => n + c.sourceCitationAccuracy, 0) / cases.length,
    totalFalsePositives: cases.reduce((n, c) => n + c.falsePositives, 0),
    totalFalseNegatives: cases.reduce((n, c) => n + c.falseNegatives, 0),
    totalUnsupportedClaims: cases.reduce((n, c) => n + c.unsupportedClaims, 0),
    prohibitedWordingCount: cases.reduce(
      (n, c) => n + c.prohibitedWordingCount,
      0,
    ),
    humanReviewRequired: cases.reduce((n, c) => n + c.humanReviewRequired, 0),
  };
  return { cases, summary, source: "backend_seeded" };
}

// Phase 5: evaluation scoring.

export type EvaluationMatch = {
  evaluationMatchId: string;
  evaluationResultId: string;
  expectedFindingId: string | null;
  draftFindingId: string | null;
  matchType: string;
  matchConfidence: number;
  matchedOn: string | null;
  notes: string | null;
};

export type AiEvaluationResult = {
  evaluationResultId: string;
  projectId: string;
  reviewRunId: string;
  expectedFindingsCount: number;
  draftFindingsCount: number;
  matchedFindingsCount: number;
  unmatchedExpectedCount: number;
  extraDraftFindingsCount: number;
  citationValidityRate: number;
  humanReviewRequiredRate: number;
  prohibitedWordCount: number;
  validationFailureCount: number;
  safetyFailureCount: number;
  recall: number;
  precision: number;
  overallScore: number;
  createdAt: string;
  matches: EvaluationMatch[];
};

export type EvaluationRunResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  result?: AiEvaluationResult;
  error?: string;
};

type ApiEvaluationMatch = {
  evaluation_match_id: string;
  evaluation_result_id: string;
  expected_finding_id: string | null;
  draft_finding_id: string | null;
  match_type: string;
  match_confidence: number;
  matched_on: string | null;
  notes: string | null;
};

type ApiEvaluationResult = {
  evaluation_result_id: string;
  project_id: string;
  review_run_id: string;
  expected_findings_count: number;
  draft_findings_count: number;
  matched_findings_count: number;
  unmatched_expected_count: number;
  extra_draft_findings_count: number;
  citation_validity_rate: number;
  human_review_required_rate: number;
  prohibited_word_count: number;
  validation_failure_count: number;
  safety_failure_count: number;
  recall: number;
  precision: number;
  overall_score: number;
  created_at: string;
  matches?: ApiEvaluationMatch[];
};

function mapEvaluationMatch(m: ApiEvaluationMatch): EvaluationMatch {
  return {
    evaluationMatchId: m.evaluation_match_id,
    evaluationResultId: m.evaluation_result_id,
    expectedFindingId: m.expected_finding_id,
    draftFindingId: m.draft_finding_id,
    matchType: m.match_type,
    matchConfidence: m.match_confidence,
    matchedOn: m.matched_on,
    notes: m.notes,
  };
}

function mapEvaluationResult(r: ApiEvaluationResult): AiEvaluationResult {
  return {
    evaluationResultId: requireString(
      r.evaluation_result_id,
      "evaluation_result_id",
    ),
    projectId: requireString(r.project_id, "project_id"),
    reviewRunId: requireString(r.review_run_id, "review_run_id"),
    expectedFindingsCount: r.expected_findings_count,
    draftFindingsCount: r.draft_findings_count,
    matchedFindingsCount: r.matched_findings_count,
    unmatchedExpectedCount: r.unmatched_expected_count,
    extraDraftFindingsCount: r.extra_draft_findings_count,
    citationValidityRate: r.citation_validity_rate,
    humanReviewRequiredRate: r.human_review_required_rate,
    prohibitedWordCount: r.prohibited_word_count,
    validationFailureCount: r.validation_failure_count,
    safetyFailureCount: r.safety_failure_count,
    recall: r.recall,
    precision: r.precision,
    overallScore: r.overall_score,
    createdAt: r.created_at,
    matches: (r.matches ?? []).map(mapEvaluationMatch),
  };
}

export async function runEvaluation(
  reviewRunId: string,
): Promise<EvaluationRunResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/ai-review-runs/${reviewRunId}/evaluate`,
      { method: "POST", headers: authHeaders(), cache: "no-store" },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Keep generic message.
      }
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      result: mapEvaluationResult((await res.json()) as ApiEvaluationResult),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to run evaluation scoring.",
    };
  }
}

export async function getRunEvaluation(
  reviewRunId: string,
): Promise<ApiResult<AiEvaluationResult>> {
  return apiGetMapped<ApiEvaluationResult, AiEvaluationResult>(
    `/api/v1/ai-review-runs/${reviewRunId}/evaluation`,
    mapEvaluationResult,
  );
}

export async function getProjectEvaluationResults(): Promise<
  ApiResult<AiEvaluationResult[]>
> {
  return apiGetMapped<ApiEvaluationResult[], AiEvaluationResult[]>(
    `/api/v1/projects/${PROJECT_ID}/ai-evaluation-results`,
    (data) => data.map(mapEvaluationResult),
  );
}

export async function getEvaluationResult(
  evaluationResultId: string,
): Promise<ApiResult<AiEvaluationResult>> {
  return apiGetMapped<ApiEvaluationResult, AiEvaluationResult>(
    `/api/v1/ai-evaluation-results/${evaluationResultId}`,
    mapEvaluationResult,
  );
}
