import { API_BASE_URL, authHeaders } from "./client";
import {
  type DashboardMetrics,
  type ReviewerQueueItem,
  type ReadResult,
  mapMetrics,
  mapQueueItem,
} from "./dashboard";

// Production Foundations Sprint 9: per-project operational metrics. These read
// access-controlled project workload summaries and pending reviewer action
// queues. Counts are operational review-support indicators only. They never
// represent approval, certification, compliance, or issue resolution.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

export type ProjectWorkloadSummary = {
  scope: string;
  generatedAt: string;
  projectId: string;
  projectName: string;
  status: string;
  sourceMode: string;
  organizationId: string | null;
  assignedReviewerUserId: string | null;
  assignedReviewerName: string | null;
  reviewPriority: string | null;
  reviewDueDate: string | null;
  lastReviewerActivityAt: string | null;
  ageBucket: string;
  dueDateIndicators: string[];
  pendingReviewerActionCount: number;
  hasPendingReviewerAction: boolean;
  metrics: DashboardMetrics;
  queue: ReviewerQueueItem[];
  accessNote: string;
};

export type ProjectPendingActions = {
  scope: string;
  generatedAt: string;
  projectId: string;
  projectName: string;
  pendingReviewerActionCount: number;
  items: ReviewerQueueItem[];
  accessNote: string;
};

function num(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

async function getJson<T>(
  path: string,
  mapper: (raw: Record<string, unknown>) => T,
): Promise<ReadResult<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      headers: authHeaders(),
    });
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const parsed = (await res.json()) as { detail?: string };
        if (parsed.detail) detail = parsed.detail;
      } catch {
        // Keep the generic message.
      }
      return {
        ok: false,
        status: res.status,
        backendReachable: true,
        error: detail,
      };
    }
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      data: mapper((await res.json()) as Record<string, unknown>),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error: "Backend unavailable. Start the API to view workload data.",
    };
  }
}

export async function getProjectWorkloadSummary(
  projectId: string,
): Promise<ReadResult<ProjectWorkloadSummary>> {
  return getJson(
    `/api/v1/projects/${projectId}/workload-summary`,
    (raw) => ({
      scope: raw.scope as string,
      generatedAt: raw.generated_at as string,
      projectId: raw.project_id as string,
      projectName: raw.project_name as string,
      status: raw.status as string,
      sourceMode: raw.source_mode as string,
      organizationId: (raw.organization_id as string) ?? null,
      assignedReviewerUserId: (raw.assigned_reviewer_user_id as string) ?? null,
      assignedReviewerName: (raw.assigned_reviewer_name as string) ?? null,
      reviewPriority: (raw.review_priority as string) ?? null,
      reviewDueDate: (raw.review_due_date as string) ?? null,
      lastReviewerActivityAt: (raw.last_reviewer_activity_at as string) ?? null,
      ageBucket: raw.age_bucket as string,
      dueDateIndicators: (raw.due_date_indicators as string[]) ?? [],
      pendingReviewerActionCount: num(raw.pending_reviewer_action_count),
      hasPendingReviewerAction: Boolean(raw.has_pending_reviewer_action),
      metrics: mapMetrics((raw.metrics as Record<string, unknown>) ?? {}),
      queue: ((raw.queue as Record<string, unknown>[]) ?? []).map(mapQueueItem),
      accessNote: raw.access_note as string,
    }),
  );
}

export async function getProjectPendingActions(
  projectId: string,
): Promise<ReadResult<ProjectPendingActions>> {
  return getJson(
    `/api/v1/projects/${projectId}/pending-actions`,
    (raw) => ({
      scope: raw.scope as string,
      generatedAt: raw.generated_at as string,
      projectId: raw.project_id as string,
      projectName: raw.project_name as string,
      pendingReviewerActionCount: num(raw.pending_reviewer_action_count),
      items: ((raw.items as Record<string, unknown>[]) ?? []).map(mapQueueItem),
      accessNote: raw.access_note as string,
    }),
  );
}
