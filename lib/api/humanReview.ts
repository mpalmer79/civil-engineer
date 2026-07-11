import { API_BASE_URL, PROJECT_ID, authHeaders,
  apiFetch,
  type ApiResult,
} from "./client";
import { mapDraft, type AiDraftFinding } from "./aiReview";

// Phase 5: human review queue and review actions.
//
// Review actions mutate backend state, so they are never faked in
// frontend-only mode. When the backend is unreachable, mutating calls return a
// clear backend-required result instead of pretending an action succeeded.

export type HumanReviewAction = {
  reviewActionId: string;
  draftFindingId: string;
  projectId: string;
  reviewRunId: string;
  reviewerName: string;
  action: string;
  reviewerNote: string;
  editedTitle: string | null;
  editedSummary: string | null;
  editedRecommendedAction: string | null;
  previousStatus: string;
  newStatus: string;
  createdAt: string;
};

export type ReviewActionInput = {
  action: string;
  reviewerName: string;
  reviewerNote: string;
  editedTitle?: string;
  editedSummary?: string;
  editedRecommendedAction?: string;
};

export type ReviewActionResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  action?: HumanReviewAction;
  draftFinding?: AiDraftFinding;
  error?: string;
};

type ApiReviewAction = {
  review_action_id: string;
  draft_finding_id: string;
  project_id: string;
  review_run_id: string;
  reviewer_name: string;
  action: string;
  reviewer_note: string;
  edited_title: string | null;
  edited_summary: string | null;
  edited_recommended_action: string | null;
  previous_status: string;
  new_status: string;
  created_at: string;
};

type ApiDraft = {
  draft_finding_id: string;
  review_run_id: string;
  project_id: string;
  checklist_item_id: string;
  finding_type: string;
  title: string;
  summary: string;
  risk_level: string;
  confidence: number;
  status: string;
  recommended_human_action: string;
  source_chunk_ids: string[];
  validation_status: string;
  safety_check_status: string;
  validation_errors: string[];
};

function mapReviewAction(a: ApiReviewAction): HumanReviewAction {
  return {
    reviewActionId: a.review_action_id,
    draftFindingId: a.draft_finding_id,
    projectId: a.project_id,
    reviewRunId: a.review_run_id,
    reviewerName: a.reviewer_name,
    action: a.action,
    reviewerNote: a.reviewer_note,
    editedTitle: a.edited_title,
    editedSummary: a.edited_summary,
    editedRecommendedAction: a.edited_recommended_action,
    previousStatus: a.previous_status,
    newStatus: a.new_status,
    createdAt: a.created_at,
  };
}

export async function getHumanReviewQueue(): Promise<ApiResult<AiDraftFinding[]>> {
  const result = await apiFetch<ApiDraft[]>(
    `/api/v1/projects/${PROJECT_ID}/human-review-queue`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: data.map(mapDraft) };
}

export async function getDraftReviewActions(
  draftFindingId: string,
): Promise<ApiResult<HumanReviewAction[]>> {
  const result = await apiFetch<ApiReviewAction[]>(
    `/api/v1/draft-findings/${draftFindingId}/review-actions`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: data.map(mapReviewAction) };
}

export async function getProjectReviewActions(): Promise<ApiResult<HumanReviewAction[]>> {
  const result = await apiFetch<ApiReviewAction[]>(
    `/api/v1/projects/${PROJECT_ID}/review-actions`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: data.map(mapReviewAction) };
}

export async function submitReviewAction(
  draftFindingId: string,
  input: ReviewActionInput,
): Promise<ReviewActionResult> {
  const payload: Record<string, string> = {
    action: input.action,
    reviewer_name: input.reviewerName,
    reviewer_note: input.reviewerNote,
  };
  if (input.editedTitle) payload.edited_title = input.editedTitle;
  if (input.editedSummary) payload.edited_summary = input.editedSummary;
  if (input.editedRecommendedAction)
    payload.edited_recommended_action = input.editedRecommendedAction;

  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/draft-findings/${draftFindingId}/review-actions`,
      {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(payload),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Non-JSON error body. Keep the generic message.
      }
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    const body = (await res.json()) as {
      action: ApiReviewAction;
      draft_finding: ApiDraft;
    };
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      action: mapReviewAction(body.action),
      draftFinding: mapDraft(body.draft_finding),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to record review actions. Review actions are never simulated in the browser.",
    };
  }
}
