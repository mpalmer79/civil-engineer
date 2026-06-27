import { API_BASE_URL, authHeaders } from "./client";

// Production Foundations Sprint 9: reviewer dashboard, workload management, and
// operational metrics. This client reads access-controlled, backend-canonical
// review-support indicators. Counts are operational only. They never represent
// approval, certification, compliance, or issue resolution.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself. Protected routes send the stored
// bearer token via authHeaders().

export type DashboardMetrics = {
  documentsUploaded: number;
  documentsNeedingIndexing: number;
  documentsIndexedWithText: number;
  documentsExtractionUnavailable: number;
  findingsNeedingReviewerConfirmation: number;
  evidenceCandidatesNeedingTriage: number;
  checklistItemsMissingEvidence: number;
  checklistItemsUnclearEvidence: number;
  applicantResponsesNeedingReview: number;
  resubmittalRoundsRegistered: number;
  matrixItemsCarriedForward: number;
  responsePackagesDraft: number;
  responsePackagesReadyForHandoff: number;
  packagesIssuedByReviewer: number;
  pendingReviewerActionCount: number;
  hasPendingReviewerAction: boolean;
};

export type DashboardAggregate = Omit<
  DashboardMetrics,
  "hasPendingReviewerAction"
>;

export type DashboardProjectSummary = {
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
};

export type ReviewerQueueItem = {
  queueItemId: string;
  projectId: string;
  projectName: string;
  itemType: string;
  label: string;
  count: number;
  status: string;
  ageBucket: string;
  targetPath: string;
};

export type ReviewerDashboard = {
  scope: string;
  generatedAt: string;
  userId: string;
  displayName: string;
  accessibleProjectCount: number;
  projectsWithPendingActionCount: number;
  totals: DashboardAggregate;
  projects: DashboardProjectSummary[];
  queue: ReviewerQueueItem[];
  accessNote: string;
};

export type ReviewerQueue = {
  scope: string;
  generatedAt: string;
  itemCount: number;
  items: ReviewerQueueItem[];
};

export type OrganizationReviewerWorkload = {
  assignedReviewerUserId: string | null;
  assignedReviewerName: string;
  projectCount: number;
  pendingReviewerActionCount: number;
  projectsWithPendingActionCount: number;
};

export type OrganizationDashboard = {
  scope: string;
  generatedAt: string;
  organizationId: string;
  organizationName: string;
  viewerRole: string;
  projectCount: number;
  projectsWithPendingActionCount: number;
  statusCounts: Record<string, number>;
  priorityCounts: Record<string, number>;
  totals: DashboardAggregate;
  projects: DashboardProjectSummary[];
  accessNote: string;
};

export type OrganizationWorkload = {
  scope: string;
  generatedAt: string;
  organizationId: string;
  organizationName: string;
  projectCount: number;
  projectsWithPendingActionCount: number;
  statusCounts: Record<string, number>;
  priorityCounts: Record<string, number>;
  totals: DashboardAggregate;
  accessNote: string;
};

export type OrganizationReviewerWorkloadResult = {
  scope: string;
  generatedAt: string;
  organizationId: string;
  organizationName: string;
  viewerRole: string;
  reviewers: OrganizationReviewerWorkload[];
  accessNote: string;
};

// A read result that preserves the HTTP status so pages can distinguish a
// permission denial (403) or sign-in requirement (401) from a network outage.
export type ReadResult<T> = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function num(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

function mapMetrics(m: Record<string, unknown>): DashboardMetrics {
  return {
    documentsUploaded: num(m.documents_uploaded),
    documentsNeedingIndexing: num(m.documents_needing_indexing),
    documentsIndexedWithText: num(m.documents_indexed_with_text),
    documentsExtractionUnavailable: num(m.documents_extraction_unavailable),
    findingsNeedingReviewerConfirmation: num(
      m.findings_needing_reviewer_confirmation,
    ),
    evidenceCandidatesNeedingTriage: num(m.evidence_candidates_needing_triage),
    checklistItemsMissingEvidence: num(m.checklist_items_missing_evidence),
    checklistItemsUnclearEvidence: num(m.checklist_items_unclear_evidence),
    applicantResponsesNeedingReview: num(m.applicant_responses_needing_review),
    resubmittalRoundsRegistered: num(m.resubmittal_rounds_registered),
    matrixItemsCarriedForward: num(m.matrix_items_carried_forward),
    responsePackagesDraft: num(m.response_packages_draft),
    responsePackagesReadyForHandoff: num(m.response_packages_ready_for_handoff),
    packagesIssuedByReviewer: num(m.packages_issued_by_reviewer),
    pendingReviewerActionCount: num(m.pending_reviewer_action_count),
    hasPendingReviewerAction: Boolean(m.has_pending_reviewer_action),
  };
}

function mapSummary(s: Record<string, unknown>): DashboardProjectSummary {
  return {
    projectId: s.project_id as string,
    projectName: s.project_name as string,
    status: s.status as string,
    sourceMode: s.source_mode as string,
    organizationId: (s.organization_id as string) ?? null,
    assignedReviewerUserId: (s.assigned_reviewer_user_id as string) ?? null,
    assignedReviewerName: (s.assigned_reviewer_name as string) ?? null,
    reviewPriority: (s.review_priority as string) ?? null,
    reviewDueDate: (s.review_due_date as string) ?? null,
    lastReviewerActivityAt: (s.last_reviewer_activity_at as string) ?? null,
    ageBucket: s.age_bucket as string,
    dueDateIndicators: (s.due_date_indicators as string[]) ?? [],
    pendingReviewerActionCount: num(s.pending_reviewer_action_count),
    hasPendingReviewerAction: Boolean(s.has_pending_reviewer_action),
    metrics: mapMetrics((s.metrics as Record<string, unknown>) ?? {}),
  };
}

function mapQueueItem(q: Record<string, unknown>): ReviewerQueueItem {
  return {
    queueItemId: q.queue_item_id as string,
    projectId: q.project_id as string,
    projectName: q.project_name as string,
    itemType: q.item_type as string,
    label: q.label as string,
    count: num(q.count),
    status: q.status as string,
    ageBucket: q.age_bucket as string,
    targetPath: q.target_path as string,
  };
}

function mapAggregate(t: Record<string, unknown>): DashboardAggregate {
  const full = mapMetrics(t);
  const { hasPendingReviewerAction: _drop, ...rest } = full;
  void _drop;
  return rest;
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
      error: "Backend unavailable. Start the API to view dashboard data.",
    };
  }
}

async function patchJson<T>(
  path: string,
  body: unknown,
  mapper: (raw: Record<string, unknown>) => T,
): Promise<MutationResult<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "PATCH",
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
      error: "Backend unavailable. Start the API to update the project.",
    };
  }
}

export async function getReviewerDashboard(): Promise<
  ReadResult<ReviewerDashboard>
> {
  return getJson("/api/v1/dashboard/reviewer", (raw) => ({
    scope: raw.scope as string,
    generatedAt: raw.generated_at as string,
    userId: raw.user_id as string,
    displayName: raw.display_name as string,
    accessibleProjectCount: num(raw.accessible_project_count),
    projectsWithPendingActionCount: num(raw.projects_with_pending_action_count),
    totals: mapAggregate((raw.totals as Record<string, unknown>) ?? {}),
    projects: ((raw.projects as Record<string, unknown>[]) ?? []).map(
      mapSummary,
    ),
    queue: ((raw.queue as Record<string, unknown>[]) ?? []).map(mapQueueItem),
    accessNote: raw.access_note as string,
  }));
}

export async function getReviewerQueue(filters?: {
  itemType?: string;
}): Promise<ReadResult<ReviewerQueue>> {
  const query = filters?.itemType ? `?item_type=${filters.itemType}` : "";
  return getJson(`/api/v1/dashboard/reviewer/queue${query}`, (raw) => ({
    scope: raw.scope as string,
    generatedAt: raw.generated_at as string,
    itemCount: num(raw.item_count),
    items: ((raw.items as Record<string, unknown>[]) ?? []).map(mapQueueItem),
  }));
}

export async function getReviewerDashboardProjects(): Promise<
  ReadResult<DashboardProjectSummary[]>
> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/dashboard/reviewer/projects`,
      { cache: "no-store", headers: authHeaders() },
    );
    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        backendReachable: true,
        error: `Request failed (${res.status}).`,
      };
    }
    const raw = (await res.json()) as Record<string, unknown>[];
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      data: raw.map(mapSummary),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error: "Backend unavailable. Start the API to view dashboard data.",
    };
  }
}

export async function getOrganizationDashboard(
  organizationId: string,
): Promise<ReadResult<OrganizationDashboard>> {
  return getJson(
    `/api/v1/organizations/${organizationId}/dashboard`,
    (raw) => ({
      scope: raw.scope as string,
      generatedAt: raw.generated_at as string,
      organizationId: raw.organization_id as string,
      organizationName: raw.organization_name as string,
      viewerRole: raw.viewer_role as string,
      projectCount: num(raw.project_count),
      projectsWithPendingActionCount: num(
        raw.projects_with_pending_action_count,
      ),
      statusCounts: (raw.status_counts as Record<string, number>) ?? {},
      priorityCounts: (raw.priority_counts as Record<string, number>) ?? {},
      totals: mapAggregate((raw.totals as Record<string, unknown>) ?? {}),
      projects: ((raw.projects as Record<string, unknown>[]) ?? []).map(
        mapSummary,
      ),
      accessNote: raw.access_note as string,
    }),
  );
}

export async function getOrganizationWorkload(
  organizationId: string,
): Promise<ReadResult<OrganizationWorkload>> {
  return getJson(`/api/v1/organizations/${organizationId}/workload`, (raw) => ({
    scope: raw.scope as string,
    generatedAt: raw.generated_at as string,
    organizationId: raw.organization_id as string,
    organizationName: raw.organization_name as string,
    projectCount: num(raw.project_count),
    projectsWithPendingActionCount: num(raw.projects_with_pending_action_count),
    statusCounts: (raw.status_counts as Record<string, number>) ?? {},
    priorityCounts: (raw.priority_counts as Record<string, number>) ?? {},
    totals: mapAggregate((raw.totals as Record<string, unknown>) ?? {}),
    accessNote: raw.access_note as string,
  }));
}

export async function getOrganizationReviewerWorkload(
  organizationId: string,
): Promise<ReadResult<OrganizationReviewerWorkloadResult>> {
  return getJson(
    `/api/v1/organizations/${organizationId}/reviewers/workload`,
    (raw) => ({
      scope: raw.scope as string,
      generatedAt: raw.generated_at as string,
      organizationId: raw.organization_id as string,
      organizationName: raw.organization_name as string,
      viewerRole: raw.viewer_role as string,
      reviewers: ((raw.reviewers as Record<string, unknown>[]) ?? []).map(
        (r) => ({
          assignedReviewerUserId: (r.assigned_reviewer_user_id as string) ?? null,
          assignedReviewerName: r.assigned_reviewer_name as string,
          projectCount: num(r.project_count),
          pendingReviewerActionCount: num(r.pending_reviewer_action_count),
          projectsWithPendingActionCount: num(
            r.projects_with_pending_action_count,
          ),
        }),
      ),
      accessNote: raw.access_note as string,
    }),
  );
}

export async function updateProjectAssignment(
  projectId: string,
  payload: { assignedReviewerUserId?: string; assignedReviewerName?: string; note?: string },
): Promise<MutationResult<DashboardProjectSummary>> {
  return patchJson(
    `/api/v1/projects/${projectId}/assignment`,
    {
      assigned_reviewer_user_id: payload.assignedReviewerUserId ?? null,
      assigned_reviewer_name: payload.assignedReviewerName ?? null,
      note: payload.note ?? null,
    },
    mapSummary,
  );
}

export async function updateProjectPriority(
  projectId: string,
  payload: { reviewPriority?: string; reviewDueDate?: string | null; note?: string },
): Promise<MutationResult<DashboardProjectSummary>> {
  const body: Record<string, unknown> = {};
  if (payload.reviewPriority !== undefined)
    body.review_priority = payload.reviewPriority;
  if (payload.reviewDueDate !== undefined)
    body.review_due_date = payload.reviewDueDate;
  if (payload.note !== undefined) body.note = payload.note;
  return patchJson(
    `/api/v1/projects/${projectId}/priority`,
    body,
    mapSummary,
  );
}

// Shared mappers reused by the operationalMetrics client.
export { mapSummary, mapQueueItem, mapMetrics, getJson };
