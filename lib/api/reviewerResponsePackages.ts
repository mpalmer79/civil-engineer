import { API_BASE_URL, authHeaders, apiFetch,
  type ApiResult,
} from "./client";

// Production Foundations Sprint 8: reviewer response packages. A response package
// assembles reviewer-selected records into a controlled communication artifact and
// a deterministic comment letter draft. Issuing a package records a reviewer
// communication only. It never approves a project, certifies compliance, validates
// design, resolves an issue, or closes an issue. Read calls return null when the
// backend is unavailable; mutating calls return a clear { ok, error } result.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

export type ReviewerResponsePackage = {
  responsePackageId: string;
  projectId: string;
  responseMatrixId: string | null;
  resubmittalRoundId: string | null;
  packageTitle: string;
  packageNumber: number;
  revisionNumber: number;
  status: string;
  packageType: string;
  sourceMode: string;
  preparedByName: string | null;
  issuedByName: string | null;
  issuedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  itemCount: number;
  includedItemCount: number;
  items?: ReviewerResponsePackageItem[];
};

export type ReviewerResponsePackageItem = {
  responsePackageItemId: string;
  responsePackageId: string;
  projectId: string;
  sourceType: string;
  sourceFindingId: string | null;
  sourceChecklistItemId: string | null;
  sourceMatrixItemId: string | null;
  sourceCitationId: string | null;
  sourceDocumentId: string | null;
  itemNumber: string | null;
  category: string | null;
  reviewerCommentText: string;
  applicantResponseSummary: string | null;
  reviewerFollowUpText: string | null;
  requestedEvidence: string | null;
  citationReference: string | null;
  includeInLetter: boolean;
  sortOrder: number;
  itemStatus: string;
  createdByName: string | null;
  updatedByName: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ResponsePackagePreviewItem = {
  itemNumber: string | null;
  category: string | null;
  reviewerCommentText: string;
  requestedEvidence: string | null;
  applicantResponseSummary: string | null;
  reviewerFollowUpText: string | null;
  citationReference: string | null;
  itemStatus: string;
};

export type ResponsePackagePreview = {
  responsePackageId: string;
  projectId: string;
  projectName: string;
  packageTitle: string;
  packageType: string;
  packageNumber: number;
  revisionNumber: number;
  status: string;
  issuedByName: string | null;
  issuedAt: string | null;
  boundaryStatement: string;
  itemCount: number;
  items: ResponsePackagePreviewItem[];
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function mapItem(i: Record<string, unknown>): ReviewerResponsePackageItem {
  return {
    responsePackageItemId: i.response_package_item_id as string,
    responsePackageId: i.response_package_id as string,
    projectId: i.project_id as string,
    sourceType: i.source_type as string,
    sourceFindingId: (i.source_finding_id as string) ?? null,
    sourceChecklistItemId: (i.source_checklist_item_id as string) ?? null,
    sourceMatrixItemId: (i.source_matrix_item_id as string) ?? null,
    sourceCitationId: (i.source_citation_id as string) ?? null,
    sourceDocumentId: (i.source_document_id as string) ?? null,
    itemNumber: (i.item_number as string) ?? null,
    category: (i.category as string) ?? null,
    reviewerCommentText: (i.reviewer_comment_text as string) ?? "",
    applicantResponseSummary: (i.applicant_response_summary as string) ?? null,
    reviewerFollowUpText: (i.reviewer_follow_up_text as string) ?? null,
    requestedEvidence: (i.requested_evidence as string) ?? null,
    citationReference: (i.citation_reference as string) ?? null,
    includeInLetter: (i.include_in_letter as boolean) ?? true,
    sortOrder: (i.sort_order as number) ?? 0,
    itemStatus: i.item_status as string,
    createdByName: (i.created_by_name as string) ?? null,
    updatedByName: (i.updated_by_name as string) ?? null,
    createdAt: (i.created_at as string) ?? null,
    updatedAt: (i.updated_at as string) ?? null,
  };
}

function mapPackage(p: Record<string, unknown>): ReviewerResponsePackage {
  return {
    responsePackageId: p.response_package_id as string,
    projectId: p.project_id as string,
    responseMatrixId: (p.response_matrix_id as string) ?? null,
    resubmittalRoundId: (p.resubmittal_round_id as string) ?? null,
    packageTitle: p.package_title as string,
    packageNumber: (p.package_number as number) ?? 1,
    revisionNumber: (p.revision_number as number) ?? 0,
    status: p.status as string,
    packageType: p.package_type as string,
    sourceMode: p.source_mode as string,
    preparedByName: (p.prepared_by_name as string) ?? null,
    issuedByName: (p.issued_by_name as string) ?? null,
    issuedAt: (p.issued_at as string) ?? null,
    createdAt: (p.created_at as string) ?? null,
    updatedAt: (p.updated_at as string) ?? null,
    itemCount: (p.item_count as number) ?? 0,
    includedItemCount: (p.included_item_count as number) ?? 0,
    items: Array.isArray(p.items)
      ? (p.items as Record<string, unknown>[]).map(mapItem)
      : undefined,
  };
}

function mapPreview(p: Record<string, unknown>): ResponsePackagePreview {
  return {
    responsePackageId: p.response_package_id as string,
    projectId: p.project_id as string,
    projectName: p.project_name as string,
    packageTitle: p.package_title as string,
    packageType: p.package_type as string,
    packageNumber: (p.package_number as number) ?? 1,
    revisionNumber: (p.revision_number as number) ?? 0,
    status: p.status as string,
    issuedByName: (p.issued_by_name as string) ?? null,
    issuedAt: (p.issued_at as string) ?? null,
    boundaryStatement: p.boundary_statement as string,
    itemCount: (p.item_count as number) ?? 0,
    items: Array.isArray(p.items)
      ? (p.items as Record<string, unknown>[]).map((it) => ({
          itemNumber: (it.item_number as string) ?? null,
          category: (it.category as string) ?? null,
          reviewerCommentText: (it.reviewer_comment_text as string) ?? "",
          requestedEvidence: (it.requested_evidence as string) ?? null,
          applicantResponseSummary:
            (it.applicant_response_summary as string) ?? null,
          reviewerFollowUpText: (it.reviewer_follow_up_text as string) ?? null,
          citationReference: (it.citation_reference as string) ?? null,
          itemStatus: it.item_status as string,
        }))
      : [],
  };
}

async function postJson<T>(
  path: string,
  body: unknown,
  mapper: (raw: Record<string, unknown>) => T,
  method = "POST",
): Promise<MutationResult<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const parsed = (await res.json()) as { detail?: string };
        if (parsed.detail) detail = parsed.detail;
      } catch {
        // Keep the generic message.
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      backendReachable: true,
      data: mapper((await res.json()) as Record<string, unknown>),
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error: "Backend unavailable. Start the API to use response packages.",
    };
  }
}

const base = (projectId: string) =>
  `/api/v1/projects/${projectId}/reviewer-response-packages`;

export async function listResponsePackages(
  projectId: string,
): Promise<ApiResult<ReviewerResponsePackage[]>> {
  const result = await apiFetch<Record<string, unknown>[]>(base(projectId));
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: data.map(mapPackage) };
}

export async function createResponsePackage(
  projectId: string,
  payload?: {
    packageTitle?: string;
    packageType?: string;
    responseMatrixId?: string;
    resubmittalRoundId?: string;
  },
): Promise<MutationResult<ReviewerResponsePackage>> {
  return postJson<ReviewerResponsePackage>(
    base(projectId),
    {
      package_title: payload?.packageTitle ?? null,
      package_type: payload?.packageType ?? null,
      response_matrix_id: payload?.responseMatrixId ?? null,
      resubmittal_round_id: payload?.resubmittalRoundId ?? null,
    },
    mapPackage,
  );
}

export async function getResponsePackageDetail(
  projectId: string,
  responsePackageId: string,
): Promise<ApiResult<ReviewerResponsePackage>> {
  const result = await apiFetch<Record<string, unknown>>(
    `${base(projectId)}/${responsePackageId}`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: mapPackage(data) };
}

export async function addMatrixItemsToPackage(
  projectId: string,
  responsePackageId: string,
  matrixItemIds: string[],
): Promise<MutationResult<ReviewerResponsePackage>> {
  return postJson<ReviewerResponsePackage>(
    `${base(projectId)}/${responsePackageId}/items/matrix-items`,
    { matrix_item_ids: matrixItemIds },
    mapPackage,
  );
}

export async function addFindingsToPackage(
  projectId: string,
  responsePackageId: string,
  findingIds: string[],
): Promise<MutationResult<ReviewerResponsePackage>> {
  return postJson<ReviewerResponsePackage>(
    `${base(projectId)}/${responsePackageId}/items/findings`,
    { finding_ids: findingIds },
    mapPackage,
  );
}

export async function addChecklistItemsToPackage(
  projectId: string,
  responsePackageId: string,
  checklistItemIds: string[],
): Promise<MutationResult<ReviewerResponsePackage>> {
  return postJson<ReviewerResponsePackage>(
    `${base(projectId)}/${responsePackageId}/items/checklist-items`,
    { checklist_item_ids: checklistItemIds },
    mapPackage,
  );
}

export async function addCitationsToPackage(
  projectId: string,
  responsePackageId: string,
  citationIds: string[],
): Promise<MutationResult<ReviewerResponsePackage>> {
  return postJson<ReviewerResponsePackage>(
    `${base(projectId)}/${responsePackageId}/items/citations`,
    { citation_ids: citationIds },
    mapPackage,
  );
}

export async function addManualPackageItem(
  projectId: string,
  responsePackageId: string,
  payload: {
    reviewerCommentText: string;
    category?: string;
    requestedEvidence?: string;
  },
): Promise<MutationResult<ReviewerResponsePackage>> {
  return postJson<ReviewerResponsePackage>(
    `${base(projectId)}/${responsePackageId}/items/manual`,
    {
      reviewer_comment_text: payload.reviewerCommentText,
      category: payload.category ?? null,
      requested_evidence: payload.requestedEvidence ?? null,
    },
    mapPackage,
  );
}

export async function updateResponsePackageItem(
  projectId: string,
  packageItemId: string,
  payload: {
    reviewerCommentText?: string;
    reviewerFollowUpText?: string;
    requestedEvidence?: string;
    includeInLetter?: boolean;
    sortOrder?: number;
    itemStatus?: string;
  },
): Promise<MutationResult<ReviewerResponsePackageItem>> {
  return postJson<ReviewerResponsePackageItem>(
    `/api/v1/projects/${projectId}/reviewer-response-package-items/${packageItemId}`,
    {
      reviewer_comment_text: payload.reviewerCommentText ?? null,
      reviewer_follow_up_text: payload.reviewerFollowUpText ?? null,
      requested_evidence: payload.requestedEvidence ?? null,
      include_in_letter: payload.includeInLetter ?? null,
      sort_order: payload.sortOrder ?? null,
      item_status: payload.itemStatus ?? null,
    },
    mapItem,
    "PATCH",
  );
}

export async function previewResponsePackage(
  projectId: string,
  responsePackageId: string,
): Promise<ApiResult<ResponsePackagePreview>> {
  const result = await apiFetch<Record<string, unknown>>(
    `${base(projectId)}/${responsePackageId}/preview`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: mapPreview(data) };
}

export async function markPackageReadyForHandoff(
  projectId: string,
  responsePackageId: string,
): Promise<MutationResult<ReviewerResponsePackage>> {
  return postJson<ReviewerResponsePackage>(
    `${base(projectId)}/${responsePackageId}/ready-for-handoff`,
    {},
    mapPackage,
  );
}

export async function issueResponsePackage(
  projectId: string,
  responsePackageId: string,
  payload?: { reviewerNote?: string },
): Promise<MutationResult<ReviewerResponsePackage>> {
  return postJson<ReviewerResponsePackage>(
    `${base(projectId)}/${responsePackageId}/issue`,
    { reviewer_note: payload?.reviewerNote ?? null },
    mapPackage,
  );
}

export async function createPackageRevision(
  projectId: string,
  responsePackageId: string,
  payload?: { revisionReason?: string },
): Promise<MutationResult<ReviewerResponsePackage>> {
  return postJson<ReviewerResponsePackage>(
    `${base(projectId)}/${responsePackageId}/revisions`,
    { revision_reason: payload?.revisionReason ?? null },
    mapPackage,
  );
}
