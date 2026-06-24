import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getReadyForHandoffSummary,
  getWorkflowItem,
  getWorkflowItems,
  updateWorkflowItemStatus,
} from "@/lib/api";

function mockFetchOnce(payload: unknown, ok = true, status = 200) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  } as Response);
}

function mockFetchUnreachable() {
  globalThis.fetch = vi.fn().mockRejectedValue(new Error("backend down"));
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("workflow API mapping", () => {
  it("maps a snake_case workflow item list to the camelCase shape", async () => {
    mockFetchOnce([
      {
        workflow_item_id: "wfi_1",
        project_id: "proj_brookside_meadows",
        packet_id: "packet_1",
        packet_item_id: "item_1",
        title: "Basin outlet detail needs review",
        description: "Reviewer needs to confirm the basin outlet detail.",
        source_type: "plan_consistency_finding",
        source_id: "pcf_1",
        severity: "high",
        status: "draft",
        assigned_role: "plan_reviewer",
        reviewer_note: null,
        target_date: null,
        section_type: "plan_consistency",
        evidence_types: ["plan_sheet", "cad_metadata"],
        requires_human_review: true,
        created_at: "2026-06-24T00:00:00Z",
        updated_at: "2026-06-24T00:00:00Z",
      },
    ]);

    const items = await getWorkflowItems();

    expect(items).toHaveLength(1);
    expect(items[0].workflowItemId).toBe("wfi_1");
    expect(items[0].assignedRole).toBe("plan_reviewer");
    expect(items[0].evidenceTypes).toEqual(["plan_sheet", "cad_metadata"]);
    expect(items[0].requiresHumanReview).toBe(true);
  });

  it("maps a workflow item detail with evidence, follow-ups, and actions", async () => {
    mockFetchOnce({
      workflow_item_id: "wfi_1",
      project_id: "proj_brookside_meadows",
      packet_id: "packet_1",
      packet_item_id: "item_1",
      title: "Item",
      description: "Description",
      source_type: "finding",
      source_id: "f_1",
      severity: "medium",
      status: "needs_follow_up",
      assigned_role: "intake_reviewer",
      reviewer_note: "A note",
      target_date: "2026-07-15",
      section_type: "document_checklist",
      evidence_types: ["document"],
      requires_human_review: true,
      created_at: "2026-06-24T00:00:00Z",
      updated_at: "2026-06-24T00:00:00Z",
      evidence_links: [
        {
          evidence_link_id: "evl_1",
          item_id: "item_1",
          evidence_type: "document",
          evidence_id: "doc_1",
          relationship: "source_document",
          label: "Drainage report",
          description: null,
        },
      ],
      follow_ups: [
        {
          follow_up_id: "wf_fu_1",
          workflow_item_id: "wfi_1",
          project_id: "proj_brookside_meadows",
          requested_from: "Applicant",
          request_reason: "Need the report",
          requested_information: "Revised drainage report",
          target_date: "2026-07-15",
          status: "open",
          reviewer_name: "Town Engineer",
          created_at: "2026-06-24T00:00:00Z",
          updated_at: "2026-06-24T00:00:00Z",
        },
      ],
      actions: [
        {
          action_id: "wf_act_1",
          workflow_item_id: "wfi_1",
          project_id: "proj_brookside_meadows",
          action_type: "follow_up_requested",
          previous_status: "draft",
          new_status: "needs_follow_up",
          reviewer_note: "Need the report",
          reviewer_name: "Town Engineer",
          created_at: "2026-06-24T00:00:00Z",
        },
      ],
    });

    const detail = await getWorkflowItem("wfi_1");

    expect(detail).not.toBeNull();
    expect(detail?.evidenceLinks).toHaveLength(1);
    expect(detail?.evidenceLinks[0].label).toBe("Drainage report");
    expect(detail?.followUps[0].requestedFrom).toBe("Applicant");
    expect(detail?.actions[0].actionType).toBe("follow_up_requested");
  });

  it("maps the ready-for-handoff summary", async () => {
    mockFetchOnce({
      project_id: "proj_brookside_meadows",
      total_items: 10,
      ready_count: 2,
      outstanding_follow_up_count: 1,
      items: [],
      note: "Ready for handoff is not an approval.",
    });

    const summary = await getReadyForHandoffSummary();

    expect(summary?.readyCount).toBe(2);
    expect(summary?.outstandingFollowUpCount).toBe(1);
    expect(summary?.totalItems).toBe(10);
  });

  it("surfaces a backend error detail on a failed status update", async () => {
    mockFetchOnce({ detail: "Status 'draft' is not a valid manual transition." }, false, 422);

    const result = await updateWorkflowItemStatus("wfi_1", "draft", undefined, "Town Engineer");

    expect(result.ok).toBe(false);
    expect(result.status).toBe(422);
    expect(result.error).toContain("not a valid manual transition");
  });

  it("reports the backend unreachable on a network failure", async () => {
    mockFetchUnreachable();

    const items = await getWorkflowItems();
    expect(items).toEqual([]);

    const result = await updateWorkflowItemStatus("wfi_1", "needs_triage");
    expect(result.ok).toBe(false);
    expect(result.backendReachable).toBe(false);
  });
});
