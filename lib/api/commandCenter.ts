import {
  PROJECT_ID,
  apiGetMapped,
  apiMutate,
  requireArray,
  requireRecord,
  requireString,
  type ApiResult,
} from "./client";

// Phase 14: reviewer command center and project health dashboard. Data is
// backend-canonical. The frontend does not simulate command center data. Read
// calls return a typed ApiResult that preserves the failure status and
// category, and mutating calls return a clear backend-required result.

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

// Command center is a high-risk reviewer surface, so the read mappers assert
// the identifiers each record needs before camel-casing. A payload missing a
// required field surfaces as an explicit invalid_response failure through
// apiGetMapped instead of propagating undefined fields into the UI.
function mapSnapshot(d: Json): ProjectCommandCenterSnapshot {
  requireString(d.snapshot_id, "snapshot_id");
  requireString(d.project_id, "project_id");
  return camel<ProjectCommandCenterSnapshot>(d);
}

function mapHealthMetric(d: Json): ProjectHealthMetric {
  requireString(d.metric_id, "metric_id");
  requireString(d.label, "label");
  return camel<ProjectHealthMetric>(d);
}

function mapAttentionItem(d: Json): ReviewerAttentionItem {
  requireString(d.attention_item_id, "attention_item_id");
  requireString(d.title, "title");
  requireString(d.status, "status");
  return camel<ReviewerAttentionItem>(d);
}

function mapTimelineEvent(d: Json): ProjectTimelineEvent {
  requireString(d.timeline_event_id, "timeline_event_id");
  requireString(d.event_title, "event_title");
  return camel<ProjectTimelineEvent>(d);
}

function mapReadinessCheck(d: Json): ReviewReadinessCheck {
  requireString(d.readiness_check_id, "readiness_check_id");
  requireString(d.label, "label");
  return camel<ReviewReadinessCheck>(d);
}

function mapReviewerNote(d: Json): DashboardReviewerNote {
  requireString(d.note_id, "note_id");
  requireString(d.note_text, "note_text");
  return camel<DashboardReviewerNote>(d);
}

function mapNextSteps(d: Json): ReviewerNextSteps {
  requireString(d.project_id, "project_id");
  const base = camel<ReviewerNextSteps>(d);
  base.steps = requireArray(d.steps ?? [], "steps").map((s) =>
    camel<ReviewerNextStep>(s as Json),
  );
  return base;
}

function mapModuleLinks(d: Json): ProjectModuleLinks {
  requireString(d.project_id, "project_id");
  const base = camel<ProjectModuleLinks>(d);
  base.links = requireArray(d.links ?? [], "links").map((l) =>
    camel<ProjectModuleLink>(l as Json),
  );
  return base;
}

function mapHealthSummary(d: Json): ProjectHealthSummary {
  requireString(d.project_id, "project_id");
  requireString(d.overall_status, "overall_status");
  return camel<ProjectHealthSummary>(d);
}

// Thin adapter over the shared mutation helper that keeps this module's
// unavailable-backend message.
async function postJson<T>(
  path: string,
  body: unknown,
): Promise<{ ok: boolean; backendReachable: boolean; data?: T; error?: string }> {
  return apiMutate<T>("POST", path, {
    body,
    unavailableMessage:
      "The backend is not reachable. The command center is not simulated in the browser.",
  });
}

export async function generateCommandCenterSnapshot(
  projectId: string = PROJECT_ID,
): Promise<{
  ok: boolean;
  backendReachable: boolean;
  data?: ProjectCommandCenterSnapshot;
  error?: string;
}> {
  const result = await postJson<Json>(
    `/api/v1/projects/${projectId}/command-center/snapshot`,
    undefined,
  );
  return {
    ...result,
    data: result.data
      ? camel<ProjectCommandCenterSnapshot>(result.data)
      : undefined,
  };
}

export async function getProjectCommandCenter(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<ProjectCommandCenterPayload>> {
  return apiGetMapped<Json, ProjectCommandCenterPayload>(
    `/api/v1/projects/${projectId}/command-center`,
    (data) => ({
      snapshot: mapSnapshot(requireRecord(data.snapshot, "snapshot")),
      healthMetrics: requireArray(data.health_metrics, "health_metrics").map(
        (m) => mapHealthMetric(m as Json),
      ),
      attentionItems: requireArray(data.attention_items, "attention_items").map(
        (a) => mapAttentionItem(a as Json),
      ),
      timeline: requireArray(data.timeline, "timeline").map((e) =>
        mapTimelineEvent(e as Json),
      ),
      readinessChecks: requireArray(
        data.readiness_checks,
        "readiness_checks",
      ).map((c) => mapReadinessCheck(c as Json)),
      nextSteps: mapNextSteps(requireRecord(data.next_steps, "next_steps")),
      moduleLinks: mapModuleLinks(
        requireRecord(data.module_links, "module_links"),
      ),
      reviewerNotes: requireArray(data.reviewer_notes, "reviewer_notes").map(
        (n) => mapReviewerNote(n as Json),
      ),
      limitationsNote: (data.limitations_note as string) ?? "",
    }),
  );
}

export async function getLatestCommandCenterSnapshot(): Promise<
  ApiResult<ProjectCommandCenterSnapshot>
> {
  return apiGetMapped<Json, ProjectCommandCenterSnapshot>(
    `/api/v1/projects/${PROJECT_ID}/command-center/latest`,
    mapSnapshot,
  );
}

export async function getProjectHealthMetrics(): Promise<
  ApiResult<ProjectHealthMetric[]>
> {
  return apiGetMapped<Json[], ProjectHealthMetric[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/health-metrics`,
    (data) =>
      requireArray(data, "health_metrics").map((m) =>
        mapHealthMetric(m as Json),
      ),
  );
}

export async function getReviewerAttentionItems(filters?: {
  status?: string;
  severity?: string;
  sourceModule?: string;
  attentionType?: string;
}): Promise<ApiResult<ReviewerAttentionItem[]>> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.severity) params.set("severity", filters.severity);
  if (filters?.sourceModule) params.set("source_module", filters.sourceModule);
  if (filters?.attentionType) params.set("attention_type", filters.attentionType);
  const query = params.toString();
  return apiGetMapped<Json[], ReviewerAttentionItem[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/attention-items${
      query ? `?${query}` : ""
    }`,
    (data) =>
      requireArray(data, "attention_items").map((a) =>
        mapAttentionItem(a as Json),
      ),
  );
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
  return apiMutate<ReviewerAttentionItem>(
    "PATCH",
    `/api/v1/command-center/attention-items/${attentionItemId}/status`,
    {
      body: {
        status,
        reviewer_name: reviewerName,
        reviewer_note: reviewerNote ?? null,
      },
      map: (raw) => camel<ReviewerAttentionItem>(raw),
      unavailableMessage: "The backend is not reachable.",
    },
  );
}

export async function getProjectTimeline(): Promise<
  ApiResult<ProjectTimelineEvent[]>
> {
  return apiGetMapped<Json[], ProjectTimelineEvent[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/timeline`,
    (data) =>
      requireArray(data, "timeline").map((e) => mapTimelineEvent(e as Json)),
  );
}

export async function getReviewReadinessChecks(): Promise<
  ApiResult<ReviewReadinessCheck[]>
> {
  return apiGetMapped<Json[], ReviewReadinessCheck[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/readiness-checks`,
    (data) =>
      requireArray(data, "readiness_checks").map((c) =>
        mapReadinessCheck(c as Json),
      ),
  );
}

export async function addDashboardReviewerNote(
  noteText: string,
  reviewerName = "reviewer",
  sourceContext?: string,
  projectId: string = PROJECT_ID,
): Promise<{
  ok: boolean;
  backendReachable: boolean;
  data?: DashboardReviewerNote;
  error?: string;
}> {
  const result = await postJson<Json>(
    `/api/v1/projects/${projectId}/command-center/notes`,
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

export async function getDashboardReviewerNotes(): Promise<
  ApiResult<DashboardReviewerNote[]>
> {
  return apiGetMapped<Json[], DashboardReviewerNote[]>(
    `/api/v1/projects/${PROJECT_ID}/command-center/notes`,
    (data) =>
      requireArray(data, "reviewer_notes").map((n) =>
        mapReviewerNote(n as Json),
      ),
  );
}

export async function getReviewerNextSteps(): Promise<
  ApiResult<ReviewerNextSteps>
> {
  return apiGetMapped<Json, ReviewerNextSteps>(
    `/api/v1/projects/${PROJECT_ID}/command-center/next-steps`,
    mapNextSteps,
  );
}

export async function getProjectModuleLinks(): Promise<
  ApiResult<ProjectModuleLinks>
> {
  return apiGetMapped<Json, ProjectModuleLinks>(
    `/api/v1/projects/${PROJECT_ID}/command-center/module-links`,
    mapModuleLinks,
  );
}

export async function getProjectHealthSummary(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<ProjectHealthSummary>> {
  return apiGetMapped<Json, ProjectHealthSummary>(
    `/api/v1/projects/${projectId}/command-center/health-summary`,
    mapHealthSummary,
  );
}
