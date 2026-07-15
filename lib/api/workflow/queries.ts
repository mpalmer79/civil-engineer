import { PROJECT_ID, apiGetMapped, type ApiResult } from "../client";
import {
  mapAction,
  mapFollowUp,
  mapItem,
  mapItemDetail,
  type ApiWorkflowAction,
  type ApiWorkflowItem,
  type ApiWorkflowItemDetail,
  type ApiFollowUp,
} from "./mappers";
import type {
  ReadyForHandoffSummary,
  WorkflowBoardSummary,
  WorkflowItem,
  WorkflowItemDetail,
  WorkflowItemHistory,
} from "./types";

// Read calls return a typed ApiResult that preserves the failure status and
// category so callers can render explicit failure states instead of
// substituting simulated workflow data.

export async function getWorkflowItems(
  filters?: {
    status?: string;
    severity?: string;
    sectionType?: string;
    assignedRole?: string;
    sourceType?: string;
  },
  projectId: string = PROJECT_ID,
): Promise<ApiResult<WorkflowItem[]>> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.severity) params.set("severity", filters.severity);
  if (filters?.sectionType) params.set("section_type", filters.sectionType);
  if (filters?.assignedRole) params.set("assigned_role", filters.assignedRole);
  if (filters?.sourceType) params.set("source_type", filters.sourceType);
  const query = params.toString();
  return apiGetMapped<ApiWorkflowItem[], WorkflowItem[]>(
    `/api/v1/projects/${projectId}/workflow-board${query ? `?${query}` : ""}`,
    (data) => data.map(mapItem),
  );
}

export async function getWorkflowItem(
  workflowItemId: string,
): Promise<ApiResult<WorkflowItemDetail>> {
  return apiGetMapped<ApiWorkflowItemDetail, WorkflowItemDetail>(
    `/api/v1/workflow-items/${workflowItemId}`,
    mapItemDetail,
  );
}

export async function getWorkflowItemHistory(
  workflowItemId: string,
): Promise<ApiResult<WorkflowItemHistory>> {
  return apiGetMapped<
    {
      workflow_item_id: string;
      project_id: string;
      actions: ApiWorkflowAction[];
      follow_ups: ApiFollowUp[];
      note: string;
    },
    WorkflowItemHistory
  >(`/api/v1/workflow-items/${workflowItemId}/history`, (data) => ({
    workflowItemId: data.workflow_item_id,
    projectId: data.project_id,
    actions: (data.actions ?? []).map(mapAction),
    followUps: (data.follow_ups ?? []).map(mapFollowUp),
    note: data.note,
  }));
}

export async function getWorkflowBoardSummary(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<WorkflowBoardSummary>> {
  return apiGetMapped<
    {
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
    },
    WorkflowBoardSummary
  >(`/api/v1/projects/${projectId}/workflow-board/summary`, (data) => ({
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
  }));
}

export async function getReadyForHandoffSummary(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<ReadyForHandoffSummary>> {
  return apiGetMapped<
    {
      project_id: string;
      total_items: number;
      ready_count: number;
      outstanding_follow_up_count: number;
      items: ApiWorkflowItem[];
      note: string;
    },
    ReadyForHandoffSummary
  >(`/api/v1/projects/${projectId}/workflow-board/ready-for-handoff`, (data) => ({
    projectId: data.project_id,
    totalItems: data.total_items,
    readyCount: data.ready_count,
    outstandingFollowUpCount: data.outstanding_follow_up_count,
    items: (data.items ?? []).map(mapItem),
    note: data.note,
  }));
}
