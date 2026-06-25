import { API_BASE_URL, PROJECT_ID, safeFetch } from "./client";

// Phase 13: multi-round resubmittal, revision comparison, and applicant response
// cycle. Data is backend-canonical. The frontend does not simulate review cycle
// data. Read calls return null or empty results when the backend is unavailable,
// and mutating calls return a clear backend-required result.

export type ReviewCycle = {
  reviewCycleId: string;
  projectId: string;
  cycleNumber: number;
  cycleName: string;
  status: string;
  startedAt: string;
  completedAt: string | null;
  sourceResponsePackageId: string | null;
  sourceWorkflowBoardId: string | null;
  summary: string;
  requiresHumanReview: boolean;
  createdAt: string;
  updatedAt: string;
};

export type ResubmittalDocument = {
  resubmittalDocumentId: string;
  projectId: string;
  reviewCycleId: string;
  resubmittalPackageId: string;
  documentType: string;
  sourceType: string;
  sourceId: string | null;
  fileName: string | null;
  description: string;
  status: string;
  createdAt: string;
};

export type ApplicantResponse = {
  applicantResponseId: string;
  projectId: string;
  reviewCycleId: string;
  resubmittalPackageId: string;
  responseText: string;
  responseTopic: string;
  submittedBy: string;
  targetResponseItemId: string | null;
  targetWorkflowItemId: string | null;
  status: string;
  reviewerNote: string | null;
  requiresHumanReview: boolean;
  createdAt: string;
  updatedAt: string;
};

export type ResubmittalPackage = {
  resubmittalPackageId: string;
  projectId: string;
  reviewCycleId: string;
  packageName: string;
  submittedBy: string;
  submittedAt: string | null;
  receivedAt: string;
  status: string;
  summary: string;
  reviewerNote: string | null;
  requiresHumanReview: boolean;
  createdAt: string;
  updatedAt: string;
  documents?: ResubmittalDocument[];
  applicantResponses?: ApplicantResponse[];
};

export type ApplicantResponseMapping = {
  mappingId: string;
  projectId: string;
  reviewCycleId: string;
  applicantResponseId: string;
  responsePackageItemId: string | null;
  workflowItemId: string | null;
  responseResolutionRecordId: string | null;
  mappingConfidence: string;
  mappingReason: string;
  requiresHumanReview: boolean;
  createdAt: string;
};

export type RevisionComparisonRun = {
  comparisonRunId: string;
  projectId: string;
  reviewCycleId: string;
  resubmittalPackageId: string | null;
  previousParseRunId: string;
  currentParseRunId: string;
  status: string;
  startedAt: string;
  completedAt: string | null;
  comparedLayerCount: number;
  comparedTextCount: number;
  addedCount: number;
  removedCount: number;
  changedCount: number;
  unchangedCount: number;
  warningCount: number;
  summary: string;
  limitationsNote: string;
  requiresHumanReview: boolean;
};

export type RevisionChangeRecord = {
  changeRecordId: string;
  projectId: string;
  reviewCycleId: string;
  comparisonRunId: string;
  changeType: string;
  sourceCategory: string;
  previousValue: string | null;
  currentValue: string | null;
  normalizedKey: string;
  layerName: string | null;
  referenceType: string | null;
  severity: string;
  linkedCadReviewFindingId: string | null;
  linkedWorkflowItemId: string | null;
  reviewerStatus: string;
  reviewerNote: string | null;
  requiresHumanReview: boolean;
  createdAt: string;
};

export type IssueCarryForward = {
  carryForwardId: string;
  projectId: string;
  reviewCycleId: string;
  sourceWorkflowItemId: string | null;
  sourceResponseItemId: string | null;
  sourceCadFindingId: string | null;
  sourceRevisionChangeId: string | null;
  title: string;
  reason: string;
  carriedForwardStatus: string;
  targetWorkflowItemId: string | null;
  createdAt: string;
  reviewerName: string;
  reviewerNote: string | null;
  requiresHumanReview: boolean;
};

export type ResponseResolutionRecord = {
  resolutionRecordId: string;
  projectId: string;
  reviewCycleId: string;
  responsePackageItemId: string | null;
  workflowItemId: string | null;
  applicantResponseId: string | null;
  revisionChangeRecordId: string | null;
  status: string;
  reviewerNote: string | null;
  reviewerName: string;
  createdAt: string;
  updatedAt: string;
  requiresHumanReview: boolean;
};

export type NextCyclePreparation = {
  nextCyclePreparationId: string;
  projectId: string;
  reviewCycleId: string;
  status: string;
  summary: string;
  carriedForwardCount: number;
  needsMoreInformationCount: number;
  reviewerCheckedCount: number;
  nextResponsePackageReady: boolean;
  createdAt: string;
  updatedAt: string;
  requiresHumanReview: boolean;
};

export type ReviewCycleDashboard = {
  projectId: string;
  cycleCount: number;
  activeCycleId: string | null;
  activeCycleNumber: number | null;
  reviewCycles: ReviewCycle[];
  resubmittalCount: number;
  resubmittalStatuses: Record<string, number>;
  applicantResponseCount: number;
  unmappedResponseCount: number;
  comparisonRunCount: number;
  revisionChangeCount: number;
  carryForwardCount: number;
  resolutionCount: number;
  resolutionStatuses: Record<string, number>;
  openItemCount: number;
  nextCycleReady: boolean;
  limitationsNote: string;
};

export type ResponseMappingSummary = {
  reviewCycleId: string;
  projectId: string;
  responseCount: number;
  mappedCount: number;
  unmappedCount: number;
  suggestedCount: number;
  confidenceCounts: Record<string, number>;
  note: string;
};

export type RevisionComparisonSummary = {
  comparisonRunId: string;
  projectId: string;
  reviewCycleId: string;
  status: string;
  addedCount: number;
  removedCount: number;
  changedCount: number;
  unchangedCount: number;
  carriedForwardCount: number;
  changesByCategory: Record<string, number>;
  changesByType: Record<string, number>;
  limitationsNote: string;
  note: string;
};

export type CarryForwardSummary = {
  reviewCycleId: string;
  projectId: string;
  total: number;
  statuses: Record<string, number>;
  note: string;
};

export type ResolutionSummary = {
  reviewCycleId: string;
  projectId: string;
  total: number;
  statuses: Record<string, number>;
  note: string;
};

type Json = Record<string, unknown>;

function camel<T>(obj: Json | null | undefined): T {
  const out: Json = {};
  if (!obj) return out as T;
  for (const [key, value] of Object.entries(obj)) {
    const ck = key.replace(/_([a-z])/g, (_m, c: string) => c.toUpperCase());
    out[ck] = value;
  }
  return out as T;
}

function mapReviewCycle(d: Json): ReviewCycle {
  return camel<ReviewCycle>(d);
}

async function postJson<T>(
  path: string,
  body: unknown,
  errorPrefix: string,
): Promise<{ ok: boolean; backendReachable: boolean; data?: T; error?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const errBody = (await res.json()) as { detail?: string };
        if (errBody.detail) detail = errBody.detail;
      } catch {
        // keep generic
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    return { ok: true, backendReachable: true, data: (await res.json()) as T };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error: `${errorPrefix} The backend is not reachable. Review cycle data is not simulated in the browser.`,
    };
  }
}

async function patchJson<T>(
  path: string,
  body: unknown,
): Promise<{ ok: boolean; backendReachable: boolean; data?: T; error?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const errBody = (await res.json()) as { detail?: string };
        if (errBody.detail) detail = errBody.detail;
      } catch {
        // keep generic
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    return { ok: true, backendReachable: true, data: (await res.json()) as T };
  } catch {
    return { ok: false, backendReachable: false, error: "The backend is not reachable." };
  }
}

// Review cycle.

export async function getReviewCycles(): Promise<ReviewCycle[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/review-cycles`,
  );
  return data ? data.map(mapReviewCycle) : [];
}

export async function getReviewCycle(
  reviewCycleId: string,
): Promise<ReviewCycle | null> {
  const data = await safeFetch<Json>(`/api/v1/review-cycles/${reviewCycleId}`);
  return data ? mapReviewCycle(data) : null;
}

export async function getReviewCycleDashboard(): Promise<ReviewCycleDashboard | null> {
  const data = await safeFetch<Json>(
    `/api/v1/projects/${PROJECT_ID}/review-cycle-dashboard`,
  );
  if (!data) return null;
  const mapped = camel<ReviewCycleDashboard>(data);
  mapped.reviewCycles = ((data.review_cycles as Json[]) ?? []).map(mapReviewCycle);
  return mapped;
}

export async function getReviewCycleSummary(): Promise<Json | null> {
  return safeFetch<Json>(
    `/api/v1/projects/${PROJECT_ID}/review-cycle-summary`,
  );
}

export async function createReviewCycle(
  cycleName?: string,
): Promise<{ ok: boolean; backendReachable: boolean; data?: ReviewCycle; error?: string }> {
  const result = await postJson<Json>(
    `/api/v1/projects/${PROJECT_ID}/review-cycles`,
    { cycle_name: cycleName ?? null },
    "Could not create the review cycle.",
  );
  return { ...result, data: result.data ? mapReviewCycle(result.data) : undefined };
}

// Resubmittal.

export async function getResubmittalPackages(): Promise<ResubmittalPackage[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/resubmittals`,
  );
  return data ? data.map((d) => camel<ResubmittalPackage>(d)) : [];
}

export async function getResubmittalPackage(
  resubmittalPackageId: string,
): Promise<ResubmittalPackage | null> {
  const data = await safeFetch<Json>(
    `/api/v1/resubmittals/${resubmittalPackageId}`,
  );
  if (!data) return null;
  const mapped = camel<ResubmittalPackage>(data);
  mapped.documents = ((data.documents as Json[]) ?? []).map((d) =>
    camel<ResubmittalDocument>(d),
  );
  mapped.applicantResponses = ((data.applicant_responses as Json[]) ?? []).map(
    (d) => camel<ApplicantResponse>(d),
  );
  return mapped;
}

export async function createResubmittalPackage(
  reviewCycleId: string,
  packageName: string,
  submittedBy = "applicant",
): Promise<{ ok: boolean; backendReachable: boolean; data?: ResubmittalPackage; error?: string }> {
  const result = await postJson<Json>(
    `/api/v1/projects/${PROJECT_ID}/resubmittals`,
    {
      review_cycle_id: reviewCycleId,
      package_name: packageName,
      submitted_by: submittedBy,
    },
    "Could not create the resubmittal package.",
  );
  return {
    ...result,
    data: result.data ? camel<ResubmittalPackage>(result.data) : undefined,
  };
}

export async function updateResubmittalPackageStatus(
  resubmittalPackageId: string,
  status: string,
  reviewerNote?: string,
): Promise<{ ok: boolean; backendReachable: boolean; data?: ResubmittalPackage; error?: string }> {
  const result = await patchJson<Json>(
    `/api/v1/resubmittals/${resubmittalPackageId}/status`,
    { status, reviewer_note: reviewerNote ?? null },
  );
  return {
    ...result,
    data: result.data ? camel<ResubmittalPackage>(result.data) : undefined,
  };
}

export async function linkCadFileToResubmittal(
  resubmittalPackageId: string,
  cadFileId: string,
): Promise<{ ok: boolean; backendReachable: boolean; data?: ResubmittalPackage; error?: string }> {
  const result = await postJson<Json>(
    `/api/v1/resubmittals/${resubmittalPackageId}/cad-files/${cadFileId}`,
    undefined,
    "Could not link the CAD file.",
  );
  return {
    ...result,
    data: result.data ? camel<ResubmittalPackage>(result.data) : undefined,
  };
}

export async function createApplicantResponse(
  resubmittalPackageId: string,
  responseText: string,
  responseTopic = "general",
  submittedBy = "applicant",
): Promise<{ ok: boolean; backendReachable: boolean; data?: ApplicantResponse; error?: string }> {
  const result = await postJson<Json>(
    `/api/v1/resubmittals/${resubmittalPackageId}/applicant-responses`,
    {
      response_text: responseText,
      response_topic: responseTopic,
      submitted_by: submittedBy,
    },
    "Could not add the applicant response.",
  );
  return {
    ...result,
    data: result.data ? camel<ApplicantResponse>(result.data) : undefined,
  };
}

// Applicant responses and mappings.

export async function getApplicantResponses(): Promise<ApplicantResponse[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/applicant-responses`,
  );
  return data ? data.map((d) => camel<ApplicantResponse>(d)) : [];
}

export async function createApplicantResponseMapping(
  applicantResponseId: string,
  options: {
    responsePackageItemId?: string;
    workflowItemId?: string;
    mappingConfidence?: string;
    mappingReason?: string;
  },
): Promise<{ ok: boolean; backendReachable: boolean; data?: ApplicantResponseMapping; error?: string }> {
  const result = await postJson<Json>(
    `/api/v1/applicant-responses/${applicantResponseId}/mappings`,
    {
      response_package_item_id: options.responsePackageItemId ?? null,
      workflow_item_id: options.workflowItemId ?? null,
      mapping_confidence: options.mappingConfidence ?? "medium",
      mapping_reason: options.mappingReason ?? null,
    },
    "Could not create the mapping.",
  );
  return {
    ...result,
    data: result.data ? camel<ApplicantResponseMapping>(result.data) : undefined,
  };
}

export async function suggestResponseMappings(
  reviewCycleId: string,
): Promise<{ ok: boolean; backendReachable: boolean; data?: ApplicantResponseMapping[]; error?: string }> {
  const result = await postJson<Json[]>(
    `/api/v1/review-cycles/${reviewCycleId}/suggest-response-mappings`,
    undefined,
    "Could not suggest mappings.",
  );
  return {
    ...result,
    data: result.data
      ? result.data.map((d) => camel<ApplicantResponseMapping>(d))
      : undefined,
  };
}

export async function getResponseMappingSummary(
  reviewCycleId: string,
): Promise<ResponseMappingSummary | null> {
  const data = await safeFetch<Json>(
    `/api/v1/review-cycles/${reviewCycleId}/response-mapping-summary`,
  );
  return data ? camel<ResponseMappingSummary>(data) : null;
}

// Revision comparison.

export async function runRevisionComparison(
  reviewCycleId: string,
  previousParseRunId: string,
  currentParseRunId: string,
  resubmittalPackageId?: string,
): Promise<{ ok: boolean; backendReachable: boolean; data?: RevisionComparisonRun; error?: string }> {
  const result = await postJson<Json>(
    `/api/v1/review-cycles/${reviewCycleId}/revision-comparisons`,
    {
      previous_parse_run_id: previousParseRunId,
      current_parse_run_id: currentParseRunId,
      resubmittal_package_id: resubmittalPackageId ?? null,
    },
    "Could not run the revision comparison.",
  );
  return {
    ...result,
    data: result.data ? camel<RevisionComparisonRun>(result.data) : undefined,
  };
}

export async function getRevisionComparisons(): Promise<RevisionComparisonRun[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/revision-comparisons`,
  );
  return data ? data.map((d) => camel<RevisionComparisonRun>(d)) : [];
}

export async function getRevisionComparison(
  comparisonRunId: string,
): Promise<RevisionComparisonRun | null> {
  const data = await safeFetch<Json>(
    `/api/v1/revision-comparisons/${comparisonRunId}`,
  );
  return data ? camel<RevisionComparisonRun>(data) : null;
}

export async function getRevisionChanges(
  comparisonRunId: string,
): Promise<RevisionChangeRecord[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/revision-comparisons/${comparisonRunId}/changes`,
  );
  return data ? data.map((d) => camel<RevisionChangeRecord>(d)) : [];
}

export async function getRevisionComparisonSummary(
  comparisonRunId: string,
): Promise<RevisionComparisonSummary | null> {
  const data = await safeFetch<Json>(
    `/api/v1/revision-comparisons/${comparisonRunId}/summary`,
  );
  return data ? camel<RevisionComparisonSummary>(data) : null;
}

// Carry-forward.

export async function carryForwardUnresolvedItems(
  reviewCycleId: string,
): Promise<{ ok: boolean; backendReachable: boolean; createdCount?: number; skippedCount?: number; error?: string }> {
  const result = await postJson<Json>(
    `/api/v1/review-cycles/${reviewCycleId}/carry-forward`,
    undefined,
    "Could not carry items forward.",
  );
  return {
    ok: result.ok,
    backendReachable: result.backendReachable,
    error: result.error,
    createdCount: result.data?.created_count as number | undefined,
    skippedCount: result.data?.skipped_count as number | undefined,
  };
}

export async function getCarryForwards(): Promise<IssueCarryForward[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/carry-forwards`,
  );
  return data ? data.map((d) => camel<IssueCarryForward>(d)) : [];
}

export async function getCarryForwardSummary(
  reviewCycleId: string,
): Promise<CarryForwardSummary | null> {
  const data = await safeFetch<Json>(
    `/api/v1/review-cycles/${reviewCycleId}/carry-forward-summary`,
  );
  return data ? camel<CarryForwardSummary>(data) : null;
}

// Resolution.

export async function createResponseResolutionRecord(
  reviewCycleId: string,
  status: string,
  options: {
    responsePackageItemId?: string;
    workflowItemId?: string;
    applicantResponseId?: string;
    revisionChangeRecordId?: string;
    reviewerNote?: string;
    reviewerName?: string;
  } = {},
): Promise<{ ok: boolean; backendReachable: boolean; data?: ResponseResolutionRecord; error?: string }> {
  const result = await postJson<Json>(
    `/api/v1/review-cycles/${reviewCycleId}/resolution-records`,
    {
      response_package_item_id: options.responsePackageItemId ?? null,
      workflow_item_id: options.workflowItemId ?? null,
      applicant_response_id: options.applicantResponseId ?? null,
      revision_change_record_id: options.revisionChangeRecordId ?? null,
      status,
      reviewer_note: options.reviewerNote ?? null,
      reviewer_name: options.reviewerName ?? "reviewer",
    },
    "Could not create the resolution record.",
  );
  return {
    ...result,
    data: result.data ? camel<ResponseResolutionRecord>(result.data) : undefined,
  };
}

export async function updateResponseResolutionStatus(
  resolutionRecordId: string,
  status: string,
  reviewerName = "reviewer",
  reviewerNote?: string,
): Promise<{ ok: boolean; backendReachable: boolean; data?: ResponseResolutionRecord; error?: string }> {
  const result = await patchJson<Json>(
    `/api/v1/resolution-records/${resolutionRecordId}/status`,
    { status, reviewer_name: reviewerName, reviewer_note: reviewerNote ?? null },
  );
  return {
    ...result,
    data: result.data ? camel<ResponseResolutionRecord>(result.data) : undefined,
  };
}

export async function getResponseResolutionRecords(): Promise<ResponseResolutionRecord[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/resolution-records`,
  );
  return data ? data.map((d) => camel<ResponseResolutionRecord>(d)) : [];
}

export async function getResolutionSummary(
  reviewCycleId: string,
): Promise<ResolutionSummary | null> {
  const data = await safeFetch<Json>(
    `/api/v1/review-cycles/${reviewCycleId}/resolution-summary`,
  );
  return data ? camel<ResolutionSummary>(data) : null;
}

// Next cycle.

export async function prepareNextCycle(
  reviewCycleId: string,
): Promise<{ ok: boolean; backendReachable: boolean; data?: NextCyclePreparation; error?: string }> {
  const result = await postJson<Json>(
    `/api/v1/review-cycles/${reviewCycleId}/prepare-next-cycle`,
    undefined,
    "Could not prepare the next cycle.",
  );
  return {
    ...result,
    data: result.data ? camel<NextCyclePreparation>(result.data) : undefined,
  };
}

export async function getNextCyclePreparation(
  reviewCycleId: string,
): Promise<NextCyclePreparation | null> {
  const data = await safeFetch<Json>(
    `/api/v1/review-cycles/${reviewCycleId}/next-cycle-preparation`,
  );
  return data ? camel<NextCyclePreparation>(data) : null;
}
