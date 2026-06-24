import { API_BASE_URL, PROJECT_ID, safeFetch } from "./client";

// Phase 4: AI Review Assistant.
//
// Draft findings are backend-canonical. The AI review page reads and triggers
// runs against the backend. When the backend is unavailable these functions
// return null or empty results and the UI shows a status note.

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

function mapRun(r: ApiRun): AiReviewRun {
  return {
    reviewRunId: r.review_run_id,
    projectId: r.project_id,
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
    draftFindingId: d.draft_finding_id,
    reviewRunId: d.review_run_id,
    projectId: d.project_id,
    checklistItemId: d.checklist_item_id,
    findingType: d.finding_type,
    title: d.title,
    summary: d.summary,
    riskLevel: d.risk_level,
    confidence: d.confidence,
    status: d.status,
    recommendedHumanAction: d.recommended_human_action,
    sourceChunkIds: d.source_chunk_ids,
    validationStatus: d.validation_status,
    safetyCheckStatus: d.safety_check_status,
    validationErrors: d.validation_errors,
  };
}

export async function getProviderMode(): Promise<ProviderModeInfo | null> {
  const data = await safeFetch<{
    provider: string;
    mode: string;
    model_name: string;
    live_calls_enabled: boolean;
    detail: string;
  }>(`/api/v1/projects/${PROJECT_ID}/ai-provider-mode`);
  if (!data) return null;
  return {
    provider: data.provider,
    mode: data.mode,
    modelName: data.model_name,
    liveCallsEnabled: data.live_calls_enabled,
    detail: data.detail,
  };
}

export async function getAiReviewRuns(): Promise<AiReviewRun[]> {
  const data = await safeFetch<ApiRun[]>(
    `/api/v1/projects/${PROJECT_ID}/ai-review-runs`,
  );
  return data ? data.map(mapRun) : [];
}

export async function startAiReviewRun(): Promise<AiReviewRun | null> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${PROJECT_ID}/ai-review-runs`,
      { method: "POST", cache: "no-store" },
    );
    if (!res.ok) return null;
    return mapRun((await res.json()) as ApiRun);
  } catch {
    return null;
  }
}

export async function getRunDraftFindings(
  reviewRunId: string,
): Promise<AiDraftFinding[]> {
  const data = await safeFetch<ApiDraft[]>(
    `/api/v1/ai-review-runs/${reviewRunId}/draft-findings`,
  );
  return data ? data.map(mapDraft) : [];
}

export async function getProjectDraftFindings(): Promise<AiDraftFinding[]> {
  const data = await safeFetch<ApiDraft[]>(
    `/api/v1/projects/${PROJECT_ID}/draft-findings`,
  );
  return data ? data.map(mapDraft) : [];
}
