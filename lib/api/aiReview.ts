import {
  API_BASE_URL,
  PROJECT_ID,
  apiGetMapped,
  authHeaders,
  requireArray,
  requireString,
  type ApiResult,
} from "./client";

// Phase 4: AI Review Assistant.
//
// Draft findings are backend-canonical. The AI review page reads and triggers
// runs against the backend. Read functions return an explicit ApiResult so a
// backend failure renders as a real failure state, never as an empty run list.

export type ProviderModeInfo = {
  provider: string;
  mode: string;
  modelName: string;
  liveCallsEnabled: boolean;
  detail: string;
};

export type AiReviewRun = {
  reviewRunId: string;
  projectId: string;
  runType: string;
  provider: string;
  modelName: string;
  status: string;
  promptVersion: string;
  checklistItemCount: number;
  draftFindingsCreated: number;
  safetyFailures: number;
  startedAt: string;
  completedAt: string | null;
};

export type AiDraftFinding = {
  draftFindingId: string;
  reviewRunId: string;
  projectId: string;
  checklistItemId: string;
  findingType: string;
  title: string;
  summary: string;
  riskLevel: string;
  confidence: number;
  status: string;
  recommendedHumanAction: string;
  sourceChunkIds: string[];
  validationStatus: string;
  safetyCheckStatus: string;
  validationErrors: string[];
};

type ApiRun = {
  review_run_id: string;
  project_id: string;
  run_type: string;
  provider: string;
  model_name: string;
  status: string;
  prompt_version: string;
  checklist_item_count: number;
  draft_findings_created: number;
  safety_failures: number;
  started_at: string;
  completed_at: string | null;
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

// Draft findings feed the reviewer queue, so the required identifiers are
// asserted at runtime; apiGetMapped turns a thrown assertion into an explicit
// invalid_response failure.
function mapRun(r: ApiRun): AiReviewRun {
  return {
    reviewRunId: requireString(r.review_run_id, "review_run_id"),
    projectId: requireString(r.project_id, "project_id"),
    runType: r.run_type,
    provider: r.provider,
    modelName: r.model_name,
    status: r.status,
    promptVersion: r.prompt_version,
    checklistItemCount: r.checklist_item_count,
    draftFindingsCreated: r.draft_findings_created,
    safetyFailures: r.safety_failures,
    startedAt: r.started_at,
    completedAt: r.completed_at,
  };
}

export function mapDraft(d: ApiDraft): AiDraftFinding {
  return {
    draftFindingId: requireString(d.draft_finding_id, "draft_finding_id"),
    reviewRunId: requireString(d.review_run_id, "review_run_id"),
    projectId: requireString(d.project_id, "project_id"),
    checklistItemId: requireString(d.checklist_item_id, "checklist_item_id"),
    findingType: d.finding_type,
    title: requireString(d.title, "title"),
    summary: d.summary,
    riskLevel: d.risk_level,
    confidence: d.confidence,
    status: requireString(d.status, "status"),
    recommendedHumanAction: d.recommended_human_action,
    sourceChunkIds: requireArray(
      d.source_chunk_ids,
      "source_chunk_ids",
    ) as string[],
    validationStatus: d.validation_status,
    safetyCheckStatus: d.safety_check_status,
    validationErrors: d.validation_errors,
  };
}

type ApiProviderMode = {
  provider: string;
  mode: string;
  model_name: string;
  live_calls_enabled: boolean;
  detail: string;
};

export async function getProviderMode(): Promise<ApiResult<ProviderModeInfo>> {
  return apiGetMapped<ApiProviderMode, ProviderModeInfo>(
    `/api/v1/projects/${PROJECT_ID}/ai-provider-mode`,
    (data) => ({
      provider: data.provider,
      mode: data.mode,
      modelName: data.model_name,
      liveCallsEnabled: data.live_calls_enabled,
      detail: data.detail,
    }),
  );
}

export async function getAiReviewRuns(): Promise<ApiResult<AiReviewRun[]>> {
  return apiGetMapped<ApiRun[], AiReviewRun[]>(
    `/api/v1/projects/${PROJECT_ID}/ai-review-runs`,
    (data) => data.map(mapRun),
  );
}

export async function startAiReviewRun(): Promise<AiReviewRun | null> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${PROJECT_ID}/ai-review-runs`,
      { method: "POST", headers: authHeaders(), cache: "no-store" },
    );
    if (!res.ok) return null;
    return mapRun((await res.json()) as ApiRun);
  } catch {
    return null;
  }
}

export async function getRunDraftFindings(
  reviewRunId: string,
): Promise<ApiResult<AiDraftFinding[]>> {
  return apiGetMapped<ApiDraft[], AiDraftFinding[]>(
    `/api/v1/ai-review-runs/${reviewRunId}/draft-findings`,
    (data) => data.map(mapDraft),
  );
}

export async function getProjectDraftFindings(): Promise<
  ApiResult<AiDraftFinding[]>
> {
  return apiGetMapped<ApiDraft[], AiDraftFinding[]>(
    `/api/v1/projects/${PROJECT_ID}/draft-findings`,
    (data) => data.map(mapDraft),
  );
}
