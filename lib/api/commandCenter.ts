import { API_BASE_URL, PROJECT_ID, safeFetch } from "./client";

// Phase 14: reviewer command center and project health dashboard. Data is
// backend-canonical. The frontend does not simulate command center data. Read
// calls return null or empty results when the backend is unavailable, and
// mutating calls return a clear backend-required result.

export type ProjectCommandCenterSnapshot = {
  snapshotId: string;
  projectId: string;
  currentReviewCycleId: string | null;
  generatedAt: string;
  overallStatus: string;
  summary: string;
  attentionCount: number;
  readyForHandoffCount: number;
  carryForwardCount: number;
  needsMoreInformationCount: number;
  cadFindingsCount: number;
  resubmittalCount: number;
  openFollowUpCount: number;
  responseMappingGapCount: number;
  revisionChangeCount: number;
  requiresHumanReview: boolean;
};

export type ProjectHealthMetric = {
  metricId: string;
  snapshotId: string;
  projectId: string;
  metricType: string;
  label: string;
  value: string;
  severity: string;
  sourceModule: string;
  sourceRoute: string;
  requiresHumanReview: boolean;
};

export type ReviewerAttentionItem = {
  attentionItemId: string;
  snapshotId: string;
  projectId: string;
  title: string;
  description: string;
  attentionType: string;
  severity: string;
  sourceModule: string;
  sourceType: string;
  sourceId: string | null;
  targetRoute: string;
  recommendedNextStep: string;
  status: string;
  createdAt: string;
  requiresHumanReview: boolean;
};

export type ProjectTimelineEvent = {
  timelineEventId: string;
  projectId: string;
  eventType: string;
  eventTitle: string;
  eventDescription: string;
  sourceModule: string;
  sourceType: string;
  sourceId: string | null;
  eventTime: string;
  targetRoute: string;
  requiresHumanReview: boolean;
};

export type ReviewReadinessCheck = {
  readinessCheckId: string;
  snapshotId: string;
  projectId: string;
  checkType: string;
  label: string;
  description: string;
  status: string;
  sourceModule: string;
  sourceCount: number;
  blockerCount: number;
  recommendedNextStep: string;
  requiresHumanReview: boolean;
};

export type DashboardReviewerNote = {
  noteId: string;
  projectId: string;
  snapshotId: string | null;
  noteText: string;
  reviewerName: string;
  createdAt: string;
  sourceContext: string | null;
  requiresHumanReview: boolean;
};

export type ReviewerNextStep = {
  title: string;
  detail: string;
  severity: string;
  targetRoute: string;
  sourceModule: string;
};

export type ReviewerNextSteps = {
  projectId: string;
  snapshotId: string | null;
  steps: ReviewerNextStep[];
  note: string;
};

export type ProjectModuleLink = {
  module: string;
  label: string;
  route: string;
  description: string;
  count: number;
  severity: string;
};

export type ProjectModuleLinks = {
  projectId: string;
  links: ProjectModuleLink[];
  note: string;
};

export type ProjectHealthSummary = {
  projectId: string;
  snapshotId: string | null;
  overallStatus: string;
  currentReviewCycleId: string | null;
  attentionCount: number;
  readyForHandoffCount: number;
  carryForwardCount: number;
  needsMoreInformationCount: number;
  cadFindingsCount: number;
  resubmittalCount: number;
  openFollowUpCount: number;
  responseMappingGapCount: number;
  revisionChangeCount: number;
  readinessReadyCount: number;
  summary: string;
  limitationsNote: string;
};

export type ProjectCommandCenterPayload = {
  snapshot: ProjectCommandCenterSnapshot;
  healthMetrics: ProjectHealthMetric[];
  attentionItems: ReviewerAttentionItem[];
  timeline: ProjectTimelineEvent[];
  readinessChecks: ReviewReadinessCheck[];
  nextSteps: ReviewerNextSteps;
  moduleLinks: ProjectModuleLinks;
  reviewerNotes: DashboardReviewerNote[];
  limitationsNote: string;
};

type Json = Record<string, unknown>;

function camel<T>(obj: Json | null | undefined): T {
  const out: Json = {};
  if (!obj) return out as T;
  for (const [key, value] of Object.entries(obj)) {
    const ck = key.replace(/_([a-z])/g, (_m, c: string) => c.toUpperCase());
    out[ck] = value;
  }
  return out as T;
}

function mapSnapshot(d: Json): ProjectCommandCenterSnapshot {
  return camel<ProjectCommandCenterSnapshot>(d);
}

function mapNextSteps(d: Json | null | undefined): ReviewerNextSteps {
  const base = camel<ReviewerNextSteps>(d);
  base.steps = (((d?.steps as Json[]) ?? []).map((s) =>
    camel<ReviewerNextStep>(s),
  ));
  return base;
}

function mapModuleLinks(d: Json | null | undefined): ProjectModuleLinks {
  const base = camel<ProjectModuleLinks>(d);
  base.links = (((d?.links as Json[]) ?? []).map((l) =>
    camel<ProjectModuleLink>(l),
  ));
  return base;
}

async function postJson<T>(
  path: string,
  body: unknown,
): Promise<{ ok: boolean; backendReachable: boolean; data?: T; error?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const errBody = (await res.json()) as { detail?: string };
        if (errBody.detail) detail = errBody.detail;
      } catch {
        // keep generic
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    return { ok: true, backendReachable: true, data: (await res.json()) as T };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. The command center is not simulated in the browser.",
    };
  }
}

export async function generateCommandCenterSnapshot(): Promise<{
  ok: boolean;
  backendReachable: boolean;
  data?: ProjectCommandCenterSnapshot;
  error?: string;
}> {
  const result = await postJson<Json>(
    `/api/v1/projects/${PROJECT_ID}/command-center/snapshot`,
    undefined,
  );
  return { ...result, data: result.data ? mapSnapshot(result.data) : undefined };
}

export async function getProjectCommandCenter(): Promise<ProjectCommandCenterPayload | null> {
  const data = await safeFetch<Json>(
    `/api/v1/projects/${PROJECT_ID}/command-center`,
  );
  if (!data) return null;
  return {
    snapshot: mapSnapshot(data.snapshot as Json),
    healthMetrics: ((data.health_metrics as Json[]) ?? []).map((m) =>
      camel<ProjectHealthMetric>(m),
    ),
    attentionItems: ((data.attention_items as Json[]) ?? []).map((a) =>
      camel<ReviewerAttentionItem>(a),
    ),
    timeline: ((data.timeline as Json[]) ?? []).map((e) =>
      camel<ProjectTimelineEvent>(e),
    ),
    readinessChecks: ((data.readiness_checks as Json[]) ?? []).map((c) =>
      camel<ReviewReadinessCheck>(c),
    ),
    nextSteps: mapNextSteps(data.next_steps as Json),
    moduleLinks: mapModuleLinks(data.module_links as Json),
    reviewerNotes: ((data.reviewer_notes as Json[]) ?? []).map((n) =>
      camel<DashboardReviewerNote>(n),
    ),
    limitationsNote: (data.limitations_note as string) ?? "",
  };
}

export async function getLatestCommandCenterSnapshot(): Promise<ProjectCommandCenterSnapshot | null> {
  const data = await safeFetch<Json>(
    `/api/v1/projects/${PROJECT_ID}/command-center/latest`,
  );
  return data ? mapSnapshot(data) : null;
}

export async function getProjectHealthMetrics(): Promise<ProjectHealthMetric[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/health-metrics`,
  );
  return data ? data.map((m) => camel<ProjectHealthMetric>(m)) : [];
}

export async function getReviewerAttentionItems(filters?: {
  status?: string;
  severity?: string;
  sourceModule?: string;
  attentionType?: string;
}): Promise<ReviewerAttentionItem[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.severity) params.set("severity", filters.severity);
  if (filters?.sourceModule) params.set("source_module", filters.sourceModule);
  if (filters?.attentionType) params.set("attention_type", filters.attentionType);
  const query = params.toString();
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/attention-items${
      query ? `?${query}` : ""
    }`,
  );
  return data ? data.map((a) => camel<ReviewerAttentionItem>(a)) : [];
}

export async function updateAttentionItemStatus(
  attentionItemId: string,
  status: string,
  reviewerName = "reviewer",
  reviewerNote?: string,
): Promise<{
  ok: boolean;
  backendReachable: boolean;
  data?: ReviewerAttentionItem;
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/command-center/attention-items/${attentionItemId}/status`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status,
          reviewer_name: reviewerName,
          reviewer_note: reviewerNote ?? null,
        }),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const errBody = (await res.json()) as { detail?: string };
        if (errBody.detail) detail = errBody.detail;
      } catch {
        // keep generic
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      backendReachable: true,
      data: camel<ReviewerAttentionItem>((await res.json()) as Json),
    };
  } catch {
    return { ok: false, backendReachable: false, error: "The backend is not reachable." };
  }
}

export async function getProjectTimeline(): Promise<ProjectTimelineEvent[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/timeline`,
  );
  return data ? data.map((e) => camel<ProjectTimelineEvent>(e)) : [];
}

export async function getReviewReadinessChecks(): Promise<ReviewReadinessCheck[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/readiness-checks`,
  );
  return data ? data.map((c) => camel<ReviewReadinessCheck>(c)) : [];
}

export async function addDashboardReviewerNote(
  noteText: string,
  reviewerName = "reviewer",
  sourceContext?: string,
): Promise<{
  ok: boolean;
  backendReachable: boolean;
  data?: DashboardReviewerNote;
  error?: string;
}> {
  const result = await postJson<Json>(
    `/api/v1/projects/${PROJECT_ID}/command-center/notes`,
    {
      note_text: noteText,
      reviewer_name: reviewerName,
      source_context: sourceContext ?? null,
    },
  );
  return {
    ...result,
    data: result.data ? camel<DashboardReviewerNote>(result.data) : undefined,
  };
}

export async function getDashboardReviewerNotes(): Promise<DashboardReviewerNote[]> {
  const data = await safeFetch<Json[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/notes`,
  );
  return data ? data.map((n) => camel<DashboardReviewerNote>(n)) : [];
}

export async function getReviewerNextSteps(): Promise<ReviewerNextSteps | null> {
  const data = await safeFetch<Json>(
    `/api/v1/projects/${PROJECT_ID}/command-center/next-steps`,
  );
  return data ? mapNextSteps(data) : null;
}

export async function getProjectModuleLinks(): Promise<ProjectModuleLinks | null> {
  const data = await safeFetch<Json>(
    `/api/v1/projects/${PROJECT_ID}/command-center/module-links`,
  );
  return data ? mapModuleLinks(data) : null;
}

export async function getProjectHealthSummary(): Promise<ProjectHealthSummary | null> {
  const data = await safeFetch<Json>(
    `/api/v1/projects/${PROJECT_ID}/command-center/health-summary`,
  );
  return data ? camel<ProjectHealthSummary>(data) : null;
}
