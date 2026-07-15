import { apiFetch, apiMutate,
  type ApiResult,
} from "./client";

// Production Foundations Sprint 7: applicant response matrix. Reviewer-controlled
// response tracking across resubmittal rounds. An applicant response is recorded
// for reviewer review, never as proof and never as a final outcome. Carry-forward
// means continued review, not resolution. Read calls return null when the backend
// is unavailable; mutating calls return a clear { ok, error } result.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

export type ResponseMatrix = {
  responseMatrixId: string;
  projectId: string;
  name: string;
  currentRoundNumber: number;
  status: string;
  sourceMode: string;
  createdByName: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  itemCount: number;
  applicantResponseSummary: Record<string, number>;
  reviewerFollowUpSummary: Record<string, number>;
  carryForwardSummary: Record<string, number>;
  items?: ResponseMatrixItem[];
};

export type ResponseMatrixItem = {
  responseMatrixItemId: string;
  responseMatrixId: string;
  projectId: string;
  sourceFindingId: string | null;
  sourceChecklistItemId: string | null;
  itemNumber: string | null;
  category: string;
  reviewerCommentDraft: string;
  requestedEvidence: string | null;
  applicantResponseText: string | null;
  applicantResponseStatus: string;
  reviewerFollowUpStatus: string;
  carryForwardStatus: string;
  currentRoundNumber: number;
  carriedFromRoundNumber: number | null;
  carriedToRoundNumber: number | null;
  relatedDocumentIds: string[];
  relatedCitationIds: string[];
  reviewerNote: string | null;
  createdByName: string | null;
  updatedByName: string | null;
  sortOrder: number;
  createdAt: string | null;
  updatedAt: string | null;
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function mapMatrix(m: Record<string, unknown>): ResponseMatrix {
  return {
    responseMatrixId: m.response_matrix_id as string,
    projectId: m.project_id as string,
    name: m.name as string,
    currentRoundNumber: (m.current_round_number as number) ?? 1,
    status: m.status as string,
    sourceMode: m.source_mode as string,
    createdByName: (m.created_by_name as string) ?? null,
    createdAt: (m.created_at as string) ?? null,
    updatedAt: (m.updated_at as string) ?? null,
    itemCount: (m.item_count as number) ?? 0,
    applicantResponseSummary:
      (m.applicant_response_summary as Record<string, number>) ?? {},
    reviewerFollowUpSummary:
      (m.reviewer_follow_up_summary as Record<string, number>) ?? {},
    carryForwardSummary:
      (m.carry_forward_summary as Record<string, number>) ?? {},
    items: Array.isArray(m.items)
      ? (m.items as Record<string, unknown>[]).map(mapItem)
      : undefined,
  };
}

function mapItem(i: Record<string, unknown>): ResponseMatrixItem {
  return {
    responseMatrixItemId: i.response_matrix_item_id as string,
    responseMatrixId: i.response_matrix_id as string,
    projectId: i.project_id as string,
    sourceFindingId: (i.source_finding_id as string) ?? null,
    sourceChecklistItemId: (i.source_checklist_item_id as string) ?? null,
    itemNumber: (i.item_number as string) ?? null,
    category: i.category as string,
    reviewerCommentDraft: (i.reviewer_comment_draft as string) ?? "",
    requestedEvidence: (i.requested_evidence as string) ?? null,
    applicantResponseText: (i.applicant_response_text as string) ?? null,
    applicantResponseStatus: i.applicant_response_status as string,
    reviewerFollowUpStatus: i.reviewer_follow_up_status as string,
    carryForwardStatus: i.carry_forward_status as string,
    currentRoundNumber: (i.current_round_number as number) ?? 1,
    carriedFromRoundNumber: (i.carried_from_round_number as number) ?? null,
    carriedToRoundNumber: (i.carried_to_round_number as number) ?? null,
    relatedDocumentIds: (i.related_document_ids as string[]) ?? [],
    relatedCitationIds: (i.related_citation_ids as string[]) ?? [],
    reviewerNote: (i.reviewer_note as string) ?? null,
    createdByName: (i.created_by_name as string) ?? null,
    updatedByName: (i.updated_by_name as string) ?? null,
    sortOrder: (i.sort_order as number) ?? 0,
    createdAt: (i.created_at as string) ?? null,
    updatedAt: (i.updated_at as string) ?? null,
  };
}

// Thin adapter over the shared mutation helper that keeps this module's
// unavailable-backend message.
async function postJson<T>(
  path: string,
  body: unknown,
  mapper: (raw: Record<string, unknown>) => T,
): Promise<MutationResult<T>> {
  return apiMutate<T>("POST", path, {
    body,
    map: mapper,
    unavailableMessage:
      "Backend unavailable. Start the API to use the response matrix.",
  });
}

export async function listResponseMatrices(
  projectId: string,
): Promise<ApiResult<ResponseMatrix[]>> {
  const result = await apiFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/response-matrices`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: data.map(mapMatrix) };
}

export async function createResponseMatrix(
  projectId: string,
  payload?: { name?: string },
): Promise<MutationResult<ResponseMatrix>> {
  return postJson<ResponseMatrix>(
    `/api/v1/projects/${projectId}/response-matrices`,
    { name: payload?.name ?? null },
    mapMatrix,
  );
}

export async function getResponseMatrix(
  projectId: string,
  responseMatrixId: string,
): Promise<ApiResult<ResponseMatrix>> {
  const result = await apiFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/response-matrices/${responseMatrixId}`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: mapMatrix(data) };
}

export async function addFindingToMatrix(
  projectId: string,
  matrixId: string,
  findingId: string,
  payload?: { reviewerCommentDraft?: string },
): Promise<MutationResult<ResponseMatrixItem>> {
  return postJson<ResponseMatrixItem>(
    `/api/v1/projects/${projectId}/response-matrices/${matrixId}/items/from-finding/${findingId}`,
    { reviewer_comment_draft: payload?.reviewerCommentDraft ?? null },
    mapItem,
  );
}

export async function addChecklistItemToMatrix(
  projectId: string,
  matrixId: string,
  checklistItemId: string,
  payload?: { reviewerCommentDraft?: string },
): Promise<MutationResult<ResponseMatrixItem>> {
  return postJson<ResponseMatrixItem>(
    `/api/v1/projects/${projectId}/response-matrices/${matrixId}/items/from-checklist-item/${checklistItemId}`,
    { reviewer_comment_draft: payload?.reviewerCommentDraft ?? null },
    mapItem,
  );
}

export async function listResponseMatrixItems(
  projectId: string,
  matrixId: string,
  filters?: { applicantResponseStatus?: string },
): Promise<ApiResult<ResponseMatrixItem[]>> {
  const params = filters?.applicantResponseStatus
    ? `?applicant_response_status=${filters.applicantResponseStatus}`
    : "";
  const result = await apiFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/response-matrices/${matrixId}/items${params}`,
  );
  if (!result.ok) return result;
  return { ...result, data: result.data.map(mapItem) };
}

export async function getResponseMatrixItem(
  projectId: string,
  itemId: string,
): Promise<ApiResult<ResponseMatrixItem>> {
  const result = await apiFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/response-matrix-items/${itemId}`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: mapItem(data) };
}

export async function updateResponseMatrixItem(
  projectId: string,
  itemId: string,
  payload: {
    reviewerCommentDraft?: string;
    requestedEvidence?: string;
    reviewerNote?: string;
    applicantResponseStatus?: string;
    reviewerFollowUpStatus?: string;
  },
): Promise<MutationResult<ResponseMatrixItem>> {
  return apiMutate<ResponseMatrixItem>(
    "PATCH",
    `/api/v1/projects/${projectId}/response-matrix-items/${itemId}`,
    {
      body: {
        reviewer_comment_draft: payload.reviewerCommentDraft ?? null,
        requested_evidence: payload.requestedEvidence ?? null,
        reviewer_note: payload.reviewerNote ?? null,
        applicant_response_status: payload.applicantResponseStatus ?? null,
        reviewer_follow_up_status: payload.reviewerFollowUpStatus ?? null,
      },
      map: mapItem,
      failureMessage: (status) => `Update failed (${status}).`,
    },
  );
}

export async function recordApplicantResponse(
  projectId: string,
  itemId: string,
  payload: { applicantResponseText: string; applicantResponseStatus?: string },
): Promise<MutationResult<ResponseMatrixItem>> {
  return postJson<ResponseMatrixItem>(
    `/api/v1/projects/${projectId}/response-matrix-items/${itemId}/applicant-response`,
    {
      applicant_response_text: payload.applicantResponseText,
      applicant_response_status: payload.applicantResponseStatus ?? null,
    },
    mapItem,
  );
}

export async function linkMatrixItemDocument(
  projectId: string,
  itemId: string,
  documentId: string,
  payload?: { linkType?: string; reviewerNote?: string },
): Promise<MutationResult<Record<string, unknown>>> {
  return postJson<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/response-matrix-items/${itemId}/documents/${documentId}`,
    {
      link_type: payload?.linkType ?? "applicant_response_document",
      reviewer_note: payload?.reviewerNote ?? null,
    },
    (raw) => raw,
  );
}

export async function carryForwardMatrixItem(
  projectId: string,
  itemId: string,
  payload?: { carryForwardStatus?: string; reviewerNote?: string },
): Promise<MutationResult<ResponseMatrixItem>> {
  return postJson<ResponseMatrixItem>(
    `/api/v1/projects/${projectId}/response-matrix-items/${itemId}/carry-forward`,
    {
      carry_forward_status: payload?.carryForwardStatus ?? null,
      reviewer_note: payload?.reviewerNote ?? null,
    },
    mapItem,
  );
}
