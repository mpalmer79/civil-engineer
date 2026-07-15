import {
  PROJECT_ID,
  apiFetch,
  apiGetMapped,
  type ApiResult,
} from "../client";
import { camel, mapReviewCycleRead, type Json } from "./mappers";
import type {
  ApplicantResponse,
  CarryForwardSummary,
  IssueCarryForward,
  NextCyclePreparation,
  ResolutionSummary,
  ResponseMappingSummary,
  ResponseResolutionRecord,
  ResubmittalDocument,
  ResubmittalPackage,
  ReviewCycle,
  ReviewCycleDashboard,
  RevisionChangeRecord,
  RevisionComparisonRun,
  RevisionComparisonSummary,
} from "./types";

// Read calls return a typed ApiResult that preserves the failure category.

// Review cycle.

export async function getReviewCycles(): Promise<ApiResult<ReviewCycle[]>> {
  return apiGetMapped<Json[], ReviewCycle[]>(
    `/api/v1/projects/${PROJECT_ID}/review-cycles`,
    (data) => data.map(mapReviewCycleRead),
  );
}

export async function getReviewCycle(
  reviewCycleId: string,
): Promise<ApiResult<ReviewCycle>> {
  return apiGetMapped<Json, ReviewCycle>(
    `/api/v1/review-cycles/${reviewCycleId}`,
    mapReviewCycleRead,
  );
}

export async function getReviewCycleDashboard(): Promise<ApiResult<ReviewCycleDashboard>> {
  return apiGetMapped<Json, ReviewCycleDashboard>(
    `/api/v1/projects/${PROJECT_ID}/review-cycle-dashboard`,
    (data) => {
      const mapped = camel<ReviewCycleDashboard>(data);
      mapped.reviewCycles = ((data.review_cycles as Json[]) ?? []).map(
        mapReviewCycleRead,
      );
      return mapped;
    },
  );
}

export async function getReviewCycleSummary(): Promise<ApiResult<Json>> {
  return apiFetch<Json>(
    `/api/v1/projects/${PROJECT_ID}/review-cycle-summary`,
  );
}

// Resubmittal.

export async function getResubmittalPackages(): Promise<ApiResult<ResubmittalPackage[]>> {
  return apiGetMapped<Json[], ResubmittalPackage[]>(
    `/api/v1/projects/${PROJECT_ID}/resubmittals`,
    (data) => data.map((d) => camel<ResubmittalPackage>(d)),
  );
}

export async function getResubmittalPackage(
  resubmittalPackageId: string,
): Promise<ApiResult<ResubmittalPackage>> {
  return apiGetMapped<Json, ResubmittalPackage>(
    `/api/v1/resubmittals/${resubmittalPackageId}`,
    (data) => {
      const mapped = camel<ResubmittalPackage>(data);
      mapped.documents = ((data.documents as Json[]) ?? []).map((d) =>
        camel<ResubmittalDocument>(d),
      );
      mapped.applicantResponses = (
        (data.applicant_responses as Json[]) ?? []
      ).map((d) => camel<ApplicantResponse>(d));
      return mapped;
    },
  );
}

// Applicant responses and mappings.

export async function getApplicantResponses(): Promise<ApiResult<ApplicantResponse[]>> {
  return apiGetMapped<Json[], ApplicantResponse[]>(
    `/api/v1/projects/${PROJECT_ID}/applicant-responses`,
    (data) => data.map((d) => camel<ApplicantResponse>(d)),
  );
}

export async function getResponseMappingSummary(
  reviewCycleId: string,
): Promise<ApiResult<ResponseMappingSummary>> {
  return apiGetMapped<Json, ResponseMappingSummary>(
    `/api/v1/review-cycles/${reviewCycleId}/response-mapping-summary`,
    (data) => camel<ResponseMappingSummary>(data),
  );
}

// Revision comparison.

export async function getRevisionComparisons(): Promise<ApiResult<RevisionComparisonRun[]>> {
  return apiGetMapped<Json[], RevisionComparisonRun[]>(
    `/api/v1/projects/${PROJECT_ID}/revision-comparisons`,
    (data) => data.map((d) => camel<RevisionComparisonRun>(d)),
  );
}

export async function getRevisionComparison(
  comparisonRunId: string,
): Promise<ApiResult<RevisionComparisonRun>> {
  return apiGetMapped<Json, RevisionComparisonRun>(
    `/api/v1/revision-comparisons/${comparisonRunId}`,
    (data) => camel<RevisionComparisonRun>(data),
  );
}

export async function getRevisionChanges(
  comparisonRunId: string,
): Promise<ApiResult<RevisionChangeRecord[]>> {
  return apiGetMapped<Json[], RevisionChangeRecord[]>(
    `/api/v1/revision-comparisons/${comparisonRunId}/changes`,
    (data) => data.map((d) => camel<RevisionChangeRecord>(d)),
  );
}

export async function getRevisionComparisonSummary(
  comparisonRunId: string,
): Promise<ApiResult<RevisionComparisonSummary>> {
  return apiGetMapped<Json, RevisionComparisonSummary>(
    `/api/v1/revision-comparisons/${comparisonRunId}/summary`,
    (data) => camel<RevisionComparisonSummary>(data),
  );
}

// Carry-forward.

export async function getCarryForwards(): Promise<ApiResult<IssueCarryForward[]>> {
  return apiGetMapped<Json[], IssueCarryForward[]>(
    `/api/v1/projects/${PROJECT_ID}/carry-forwards`,
    (data) => data.map((d) => camel<IssueCarryForward>(d)),
  );
}

export async function getCarryForwardSummary(
  reviewCycleId: string,
): Promise<ApiResult<CarryForwardSummary>> {
  return apiGetMapped<Json, CarryForwardSummary>(
    `/api/v1/review-cycles/${reviewCycleId}/carry-forward-summary`,
    (data) => camel<CarryForwardSummary>(data),
  );
}

// Resolution.

export async function getResponseResolutionRecords(): Promise<ApiResult<ResponseResolutionRecord[]>> {
  return apiGetMapped<Json[], ResponseResolutionRecord[]>(
    `/api/v1/projects/${PROJECT_ID}/resolution-records`,
    (data) => data.map((d) => camel<ResponseResolutionRecord>(d)),
  );
}

export async function getResolutionSummary(
  reviewCycleId: string,
): Promise<ApiResult<ResolutionSummary>> {
  return apiGetMapped<Json, ResolutionSummary>(
    `/api/v1/review-cycles/${reviewCycleId}/resolution-summary`,
    (data) => camel<ResolutionSummary>(data),
  );
}

// Next cycle.

export async function getNextCyclePreparation(
  reviewCycleId: string,
): Promise<ApiResult<NextCyclePreparation>> {
  return apiGetMapped<Json, NextCyclePreparation>(
    `/api/v1/review-cycles/${reviewCycleId}/next-cycle-preparation`,
    (data) => camel<NextCyclePreparation>(data),
  );
}
