import { API_BASE_URL, PROJECT_ID, safeFetch } from "./client";

// Phase 9: reviewer workflow board and issue resolution tracking.
//
// Phase 9 data is backend-canonical. The frontend does not simulate workflow
// data. Read calls return null or empty results when the backend is
// unavailable, and the mutating calls return a clear backend-required result.

export type WorkflowEvidenceLink = {
  evidenceLinkId: string;
  itemId: string;
  evidenceType: string;
  evidenceId: string;
  relationship: string;
  label: string;
  description: string | null;
};

export type WorkflowAction = {
  actionId: string;
  workflowItemId: string;
  projectId: string;
  actionType: string;
  previousStatus: string;
  newStatus: string;
  reviewerNote: string;
  reviewerName: string;
  createdAt: string;
};

export type WorkflowFollowUp = {
  followUpId: string;
  workflowItemId: string;
  projectId: string;
  requestedFrom: string;
  requestReason: string;
  requestedInformation: string;
  targetDate: string | null;
  status: string;
  reviewerName: string;
  createdAt: string;
  updatedAt: string;
};

export type WorkflowItem = {
  workflowItemId: string;
  projectId: string;
  packetId: string | null;
  packetItemId: string | null;
  title: string;
  description: string;
  sourceType: string;
  sourceId: string | null;
  severity: string;
  status: string;
  assignedRole: string;
  reviewerNote: string | null;
  targetDate: string | null;
  sectionType: string;
  evidenceTypes: string[];
  requiresHumanReview: boolean;
  createdAt: string;
  updatedAt: string;
};

export type WorkflowItemDetail = WorkflowItem & {
  evidenceLinks: WorkflowEvidenceLink[];
  followUps: WorkflowFollowUp[];
  actions: WorkflowAction[];
};

export type WorkflowItemHistory = {
  workflowItemId: string;
  projectId: string;
  actions: WorkflowAction[];
  followUps: WorkflowFollowUp[];
  note: string;
};

export type WorkflowBoardSummary = {
  projectId: string;
  totalItems: number;
  itemsByStatus: Record<string, number>;
  itemsBySeverity: Record<string, number>;
  itemsBySectionType: Record<string, number>;
  itemsByAssignedRole: Record<string, number>;
  itemsRequiringHumanReview: number;
  openFollowUpCount: number;
  readyForHandoffCount: number;
  note: string;
};

export type ReadyForHandoffSummary = {
  projectId: string;
  totalItems: number;
  readyCount: number;
  outstandingFollowUpCount: number;
  items: WorkflowItem[];
  note: string;
};

export type WorkflowMutationResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  item?: WorkflowItem;
  followUp?: WorkflowFollowUp;
  error?: string;
};

type ApiWorkflowItem = {
  workflow_item_id: string;
  project_id: string;
  packet_id: string | null;
  packet_item_id: string | null;
  title: string;
  description: string;
  source_type: string;
  source_id: string | null;
  severity: string;
  status: string;
  assigned_role: string;
  reviewer_note: string | null;
  target_date: string | null;
  section_type: string;
  evidence_types: string[];
  requires_human_review: boolean;
  created_at: string;
  updated_at: string;
};

type ApiEvidenceLink = {
  evidence_link_id: string;
  item_id: string;
  evidence_type: string;
  evidence_id: string;
  relationship: string;
  label: string;
  description: string | null;
};

type ApiWorkflowAction = {
  action_id: string;
  workflow_item_id: string;
  project_id: string;
  action_type: string;
  previous_status: string;
  new_status: string;
  reviewer_note: string;
  reviewer_name: string;
  created_at: string;
};

type ApiFollowUp = {
  follow_up_id: string;
  workflow_item_id: string;
  project_id: string;
  requested_from: string;
  request_reason: string;
  requested_information: string;
  target_date: string | null;
  status: string;
  reviewer_name: string;
  created_at: string;
  updated_at: string;
};

type ApiWorkflowItemDetail = ApiWorkflowItem & {
  evidence_links: ApiEvidenceLink[];
  follow_ups: ApiFollowUp[];
  actions: ApiWorkflowAction[];
};

function mapItem(i: ApiWorkflowItem): WorkflowItem {
  return {
    workflowItemId: i.workflow_item_id,
    projectId: i.project_id,
    packetId: i.packet_id,
    packetItemId: i.packet_item_id,
    title: i.title,
    description: i.description,
    sourceType: i.source_type,
    sourceId: i.source_id,
    severity: i.severity,
    status: i.status,
    assignedRole: i.assigned_role,
    reviewerNote: i.reviewer_note,
    targetDate: i.target_date,
    sectionType: i.section_type,
    evidenceTypes: i.evidence_types ?? [],
    requiresHumanReview: i.requires_human_review,
    createdAt: i.created_at,
    updatedAt: i.updated_at,
  };
}

function mapEvidenceLink(l: ApiEvidenceLink): WorkflowEvidenceLink {
  return {
    evidenceLinkId: l.evidence_link_id,
    itemId: l.item_id,
    evidenceType: l.evidence_type,
    evidenceId: l.evidence_id,
    relationship: l.relationship,
    label: l.label,
    description: l.description,
  };
}

function mapAction(a: ApiWorkflowAction): WorkflowAction {
  return {
    actionId: a.action_id,
    workflowItemId: a.workflow_item_id,
    projectId: a.project_id,
    actionType: a.action_type,
    previousStatus: a.previous_status,
    newStatus: a.new_status,
    reviewerNote: a.reviewer_note,
    reviewerName: a.reviewer_name,
    createdAt: a.created_at,
  };
}

function mapFollowUp(f: ApiFollowUp): WorkflowFollowUp {
  return {
    followUpId: f.follow_up_id,
    workflowItemId: f.workflow_item_id,
    projectId: f.project_id,
    requestedFrom: f.requested_from,
    requestReason: f.request_reason,
    requestedInformation: f.requested_information,
    targetDate: f.target_date,
    status: f.status,
    reviewerName: f.reviewer_name,
    createdAt: f.created_at,
    updatedAt: f.updated_at,
  };
}

function mapItemDetail(i: ApiWorkflowItemDetail): WorkflowItemDetail {
  return {
    ...mapItem(i),
    evidenceLinks: (i.evidence_links ?? []).map(mapEvidenceLink),
    followUps: (i.follow_ups ?? []).map(mapFollowUp),
    actions: (i.actions ?? []).map(mapAction),
  };
}

export async function getWorkflowItems(filters?: {
  status?: string;
  severity?: string;
  sectionType?: string;
  assignedRole?: string;
  sourceType?: string;
}): Promise<WorkflowItem[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.severity) params.set("severity", filters.severity);
  if (filters?.sectionType) params.set("section_type", filters.sectionType);
  if (filters?.assignedRole) params.set("assigned_role", filters.assignedRole);
  if (filters?.sourceType) params.set("source_type", filters.sourceType);
  const query = params.toString();
  const data = await safeFetch<ApiWorkflowItem[]>(
    `/api/v1/projects/${PROJECT_ID}/workflow-board${query ? `?${query}` : ""}`,
  );
  return data ? data.map(mapItem) : [];
}

export async function getWorkflowItem(
  workflowItemId: string,
): Promise<WorkflowItemDetail | null> {
  const data = await safeFetch<ApiWorkflowItemDetail>(
    `/api/v1/workflow-items/${workflowItemId}`,
  );
  return data ? mapItemDetail(data) : null;
}

export async function getWorkflowItemHistory(
  workflowItemId: string,
): Promise<WorkflowItemHistory | null> {
  const data = await safeFetch<{
    workflow_item_id: string;
    project_id: string;
    actions: ApiWorkflowAction[];
    follow_ups: ApiFollowUp[];
    note: string;
  }>(`/api/v1/workflow-items/${workflowItemId}/history`);
  if (!data) return null;
  return {
    workflowItemId: data.workflow_item_id,
    projectId: data.project_id,
    actions: (data.actions ?? []).map(mapAction),
    followUps: (data.follow_ups ?? []).map(mapFollowUp),
    note: data.note,
  };
}

export async function getWorkflowBoardSummary(): Promise<WorkflowBoardSummary | null> {
  const data = await safeFetch<{
    project_id: string;
    total_items: number;
    items_by_status: Record<string, number>;
    items_by_severity: Record<string, number>;
    items_by_section_type: Record<string, number>;
    items_by_assigned_role: Record<string, number>;
    items_requiring_human_review: number;
    open_follow_up_count: number;
    ready_for_handoff_count: number;
    note: string;
  }>(`/api/v1/projects/${PROJECT_ID}/workflow-board/summary`);
  if (!data) return null;
  return {
    projectId: data.project_id,
    totalItems: data.total_items,
    itemsByStatus: data.items_by_status,
    itemsBySeverity: data.items_by_severity,
    itemsBySectionType: data.items_by_section_type,
    itemsByAssignedRole: data.items_by_assigned_role,
    itemsRequiringHumanReview: data.items_requiring_human_review,
    openFollowUpCount: data.open_follow_up_count,
    readyForHandoffCount: data.ready_for_handoff_count,
    note: data.note,
  };
}

export async function getReadyForHandoffSummary(): Promise<ReadyForHandoffSummary | null> {
  const data = await safeFetch<{
    project_id: string;
    total_items: number;
    ready_count: number;
    outstanding_follow_up_count: number;
    items: ApiWorkflowItem[];
    note: string;
  }>(`/api/v1/projects/${PROJECT_ID}/workflow-board/ready-for-handoff`);
  if (!data) return null;
  return {
    projectId: data.project_id,
    totalItems: data.total_items,
    readyCount: data.ready_count,
    outstandingFollowUpCount: data.outstanding_follow_up_count,
    items: (data.items ?? []).map(mapItem),
    note: data.note,
  };
}

export async function generateWorkflowBoard(): Promise<{
  ok: boolean;
  backendReachable: boolean;
  items?: WorkflowItem[];
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${PROJECT_ID}/workflow-board/generate`,
      { method: "POST", cache: "no-store" },
    );
    if (!res.ok) {
      return {
        ok: false,
        backendReachable: true,
        error: `Request failed (${res.status}).`,
      };
    }
    return {
      ok: true,
      backendReachable: true,
      items: ((await res.json()) as ApiWorkflowItem[]).map(mapItem),
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to generate the workflow board. Board data is not simulated in the browser.",
    };
  }
}

async function postMutation(
  path: string,
  method: "POST" | "PATCH",
  body: Record<string, unknown>,
  unreachableMessage: string,
): Promise<{ ok: boolean; status: number; backendReachable: boolean; data?: unknown; error?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const errBody = (await res.json()) as { detail?: string };
        if (errBody.detail) detail = errBody.detail;
      } catch {
        // Keep generic message.
      }
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    return { ok: true, status: res.status, backendReachable: true, data: await res.json() };
  } catch {
    return { ok: false, status: 0, backendReachable: false, error: unreachableMessage };
  }
}

export async function updateWorkflowItemStatus(
  workflowItemId: string,
  newStatus: string,
  reviewerNote?: string,
  reviewerName?: string,
  targetDate?: string,
): Promise<WorkflowMutationResult> {
  const result = await postMutation(
    `/api/v1/workflow-items/${workflowItemId}/status`,
    "PATCH",
    {
      new_status: newStatus,
      reviewer_note: reviewerNote,
      reviewer_name: reviewerName,
      target_date: targetDate,
    },
    "The backend is not reachable. Start the API to update a workflow item status.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    item: result.data ? mapItem(result.data as ApiWorkflowItem) : undefined,
    error: result.error,
  };
}

export async function addWorkflowNote(
  workflowItemId: string,
  reviewerNote: string,
  reviewerName: string,
): Promise<WorkflowMutationResult> {
  const result = await postMutation(
    `/api/v1/workflow-items/${workflowItemId}/notes`,
    "POST",
    { reviewer_note: reviewerNote, reviewer_name: reviewerName },
    "The backend is not reachable. Start the API to add a reviewer note.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    item: result.data ? mapItem(result.data as ApiWorkflowItem) : undefined,
    error: result.error,
  };
}

export async function createWorkflowFollowUp(
  workflowItemId: string,
  input: {
    requestedFrom: string;
    requestReason: string;
    requestedInformation: string;
    reviewerName: string;
    targetDate?: string;
  },
): Promise<WorkflowMutationResult> {
  const result = await postMutation(
    `/api/v1/workflow-items/${workflowItemId}/follow-ups`,
    "POST",
    {
      requested_from: input.requestedFrom,
      request_reason: input.requestReason,
      requested_information: input.requestedInformation,
      reviewer_name: input.reviewerName,
      target_date: input.targetDate,
    },
    "The backend is not reachable. Start the API to open a follow-up request.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    followUp: result.data ? mapFollowUp(result.data as ApiFollowUp) : undefined,
    error: result.error,
  };
}
