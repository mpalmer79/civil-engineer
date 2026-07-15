import { API_BASE_URL, PROJECT_ID, authHeaders } from "../client";
import {
  mapFollowUp,
  mapItem,
  type ApiFollowUp,
  type ApiWorkflowItem,
} from "./mappers";
import type { WorkflowItem, WorkflowMutationResult } from "./types";

// Mutating calls return a clear backend-required result. Workflow data is not
// simulated in the browser, so an unreachable backend surfaces as
// backendReachable: false with a reviewer-facing message.

export async function generateWorkflowBoard(
  projectId: string = PROJECT_ID,
): Promise<{
  ok: boolean;
  backendReachable: boolean;
  items?: WorkflowItem[];
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/workflow-board/generate`,
      { method: "POST", headers: authHeaders(), cache: "no-store" },
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
      headers: authHeaders({ "Content-Type": "application/json" }),
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
