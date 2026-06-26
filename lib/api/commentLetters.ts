import { API_BASE_URL, authHeaders, safeFetch } from "./client";

// Production Foundations Sprint 8: comment letter drafts. A comment letter draft
// is generated deterministically from a response package using fixed templates
// only. There are no live AI calls. The draft is reviewer-editable and carries a
// fixed review-support boundary statement. It does not approve plans, certify
// compliance, validate design, resolve an issue, or close an issue. Read calls
// return null when the backend is unavailable; mutating calls return a clear
// { ok, error } result.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

export type CommentLetterDraft = {
  commentLetterDraftId: string;
  responsePackageId: string;
  projectId: string;
  title: string;
  recipientName: string | null;
  recipientOrganization: string | null;
  subjectLine: string;
  introductionText: string;
  projectSummaryText: string | null;
  reviewScopeText: string | null;
  commentItemsText: string;
  resubmittalSummaryText: string | null;
  closingText: string;
  status: string;
  revisionNumber: number;
  boundaryStatement: string;
  createdByName: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type CommentLetterPreviewSection = {
  heading: string;
  body: string;
};

export type CommentLetterPreview = {
  commentLetterDraftId: string;
  responsePackageId: string;
  projectId: string;
  title: string;
  recipientName: string | null;
  recipientOrganization: string | null;
  status: string;
  revisionNumber: number;
  boundaryStatement: string;
  sections: CommentLetterPreviewSection[];
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function mapDraft(d: Record<string, unknown>): CommentLetterDraft {
  return {
    commentLetterDraftId: d.comment_letter_draft_id as string,
    responsePackageId: d.response_package_id as string,
    projectId: d.project_id as string,
    title: d.title as string,
    recipientName: (d.recipient_name as string) ?? null,
    recipientOrganization: (d.recipient_organization as string) ?? null,
    subjectLine: (d.subject_line as string) ?? "",
    introductionText: (d.introduction_text as string) ?? "",
    projectSummaryText: (d.project_summary_text as string) ?? null,
    reviewScopeText: (d.review_scope_text as string) ?? null,
    commentItemsText: (d.comment_items_text as string) ?? "",
    resubmittalSummaryText: (d.resubmittal_summary_text as string) ?? null,
    closingText: (d.closing_text as string) ?? "",
    status: d.status as string,
    revisionNumber: (d.revision_number as number) ?? 0,
    boundaryStatement: d.boundary_statement as string,
    createdByName: (d.created_by_name as string) ?? null,
    createdAt: (d.created_at as string) ?? null,
    updatedAt: (d.updated_at as string) ?? null,
  };
}

function mapPreview(p: Record<string, unknown>): CommentLetterPreview {
  return {
    commentLetterDraftId: p.comment_letter_draft_id as string,
    responsePackageId: p.response_package_id as string,
    projectId: p.project_id as string,
    title: p.title as string,
    recipientName: (p.recipient_name as string) ?? null,
    recipientOrganization: (p.recipient_organization as string) ?? null,
    status: p.status as string,
    revisionNumber: (p.revision_number as number) ?? 0,
    boundaryStatement: p.boundary_statement as string,
    sections: Array.isArray(p.sections)
      ? (p.sections as Record<string, unknown>[]).map((s) => ({
          heading: s.heading as string,
          body: s.body as string,
        }))
      : [],
  };
}

async function sendJson<T>(
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
      error: "Backend unavailable. Start the API to use comment letter drafts.",
    };
  }
}

export async function generateCommentLetterDraft(
  projectId: string,
  responsePackageId: string,
  payload?: { recipientName?: string; recipientOrganization?: string },
): Promise<MutationResult<CommentLetterDraft>> {
  return sendJson<CommentLetterDraft>(
    `/api/v1/projects/${projectId}/reviewer-response-packages/${responsePackageId}/comment-letter-draft`,
    {
      recipient_name: payload?.recipientName ?? null,
      recipient_organization: payload?.recipientOrganization ?? null,
    },
    mapDraft,
  );
}

export async function getCommentLetterDraft(
  projectId: string,
  draftId: string,
): Promise<CommentLetterDraft | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/comment-letter-drafts/${draftId}`,
  );
  return data ? mapDraft(data) : null;
}

export async function updateCommentLetterDraft(
  projectId: string,
  draftId: string,
  payload: {
    title?: string;
    recipientName?: string;
    recipientOrganization?: string;
    subjectLine?: string;
    introductionText?: string;
    projectSummaryText?: string;
    reviewScopeText?: string;
    commentItemsText?: string;
    resubmittalSummaryText?: string;
    closingText?: string;
    status?: string;
  },
): Promise<MutationResult<CommentLetterDraft>> {
  return sendJson<CommentLetterDraft>(
    `/api/v1/projects/${projectId}/comment-letter-drafts/${draftId}`,
    {
      title: payload.title ?? null,
      recipient_name: payload.recipientName ?? null,
      recipient_organization: payload.recipientOrganization ?? null,
      subject_line: payload.subjectLine ?? null,
      introduction_text: payload.introductionText ?? null,
      project_summary_text: payload.projectSummaryText ?? null,
      review_scope_text: payload.reviewScopeText ?? null,
      comment_items_text: payload.commentItemsText ?? null,
      resubmittal_summary_text: payload.resubmittalSummaryText ?? null,
      closing_text: payload.closingText ?? null,
      status: payload.status ?? null,
    },
    mapDraft,
    "PATCH",
  );
}

export async function previewCommentLetter(
  projectId: string,
  draftId: string,
): Promise<CommentLetterPreview | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/comment-letter-drafts/${draftId}/preview`,
  );
  return data ? mapPreview(data) : null;
}
