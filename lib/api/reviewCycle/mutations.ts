import { PROJECT_ID, apiMutate } from "../client";
import { camel, mapReviewCycle, type Json } from "./mappers";
import type {
  ApplicantResponse,
  ApplicantResponseMapping,
  NextCyclePreparation,
  ResponseResolutionRecord,
  ResubmittalPackage,
  ReviewCycle,
  RevisionComparisonRun,
} from "./types";

// Mutating calls return a clear backend-required result. Review cycle data is
// not simulated in the browser, so an unreachable backend surfaces as
// backendReachable: false with a reviewer-facing message.

async function postJson<T>(
  path: string,
  body: unknown,
  errorPrefix: string,
): Promise<{ ok: boolean; backendReachable: boolean; data?: T; error?: string }> {
  return apiMutate<T>("POST", path, {
    body,
    unavailableMessage: `${errorPrefix} The backend is not reachable. Review cycle data is not simulated in the browser.`,
  });
}

async function patchJson<T>(
  path: string,
  body: unknown,
): Promise<{ ok: boolean; backendReachable: boolean; data?: T; error?: string }> {
  return apiMutate<T>("PATCH", path, {
    body,
    unavailableMessage: "The backend is not reachable.",
  });
}

// Review cycle.

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
