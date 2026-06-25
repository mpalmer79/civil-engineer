import { afterEach, describe, expect, it, vi } from "vitest";

import {
  generateCommandCenterSnapshot,
  getProjectCommandCenter,
  getProjectHealthSummary,
  getReviewerAttentionItems,
  updateAttentionItemStatus,
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

describe("Phase 14 command center API mapping", () => {
  it("maps the command center payload with nested arrays and objects", async () => {
    mockFetchOnce({
      snapshot: {
        snapshot_id: "cc_1",
        project_id: "proj_brookside_meadows",
        current_review_cycle_id: "cycle_1",
        generated_at: "2026-06-25T00:00:00Z",
        overall_status: "active_review",
        summary: "Review-support summary.",
        attention_count: 3,
        ready_for_handoff_count: 1,
        carry_forward_count: 2,
        needs_more_information_count: 1,
        cad_findings_count: 4,
        resubmittal_count: 1,
        open_follow_up_count: 0,
        response_mapping_gap_count: 2,
        revision_change_count: 3,
        requires_human_review: true,
      },
      health_metrics: [
        {
          metric_id: "hm_1",
          snapshot_id: "cc_1",
          project_id: "proj_brookside_meadows",
          metric_type: "workflow_status_count",
          label: "Workflow items needing attention",
          value: "2",
          severity: "medium",
          source_module: "workflow_board",
          source_route: "/workflow-board",
          requires_human_review: true,
        },
      ],
      attention_items: [
        {
          attention_item_id: "att_1",
          snapshot_id: "cc_1",
          project_id: "proj_brookside_meadows",
          title: "Workflow item needs follow-up",
          description: "desc",
          attention_type: "workflow_item_needs_follow_up",
          severity: "medium",
          source_module: "workflow_board",
          source_type: "workflow_item",
          source_id: "wfi_1",
          target_route: "/workflow-board",
          recommended_next_step: "Open the item.",
          status: "open",
          created_at: "2026-06-25T00:00:00Z",
          requires_human_review: true,
        },
      ],
      timeline: [
        {
          timeline_event_id: "tl_1",
          project_id: "proj_brookside_meadows",
          event_type: "cad_parse_completed",
          event_title: "DXF parse run recorded",
          event_description: "desc",
          source_module: "cad_intake",
          source_type: "cad_parse_run",
          source_id: "cadrun_1",
          event_time: "2026-06-25T00:00:00Z",
          target_route: "/cad-intake",
          requires_human_review: false,
        },
      ],
      readiness_checks: [
        {
          readiness_check_id: "rc_1",
          snapshot_id: "cc_1",
          project_id: "proj_brookside_meadows",
          check_type: "human_review_signoff",
          label: "Human review signoff still required",
          description: "desc",
          status: "ready_for_human_review",
          source_module: "human_review",
          source_count: 1,
          blocker_count: 1,
          recommended_next_step: "Route to a licensed PE.",
          requires_human_review: true,
        },
      ],
      next_steps: {
        project_id: "proj_brookside_meadows",
        snapshot_id: "cc_1",
        steps: [
          {
            title: "Open the item",
            detail: "detail",
            severity: "medium",
            target_route: "/workflow-board",
            source_module: "workflow_board",
          },
        ],
        note: "review support only",
      },
      module_links: {
        project_id: "proj_brookside_meadows",
        links: [
          {
            module: "cad_intake",
            label: "CAD Intake",
            route: "/cad-intake",
            description: "desc",
            count: 2,
            severity: "medium",
          },
        ],
        note: "links into modules",
      },
      reviewer_notes: [],
      limitations_note: "does not approve",
    });

    const payload = await getProjectCommandCenter();
    expect(payload?.snapshot.overallStatus).toBe("active_review");
    expect(payload?.healthMetrics[0].sourceRoute).toBe("/workflow-board");
    expect(payload?.attentionItems[0].attentionType).toBe(
      "workflow_item_needs_follow_up",
    );
    expect(payload?.timeline[0].eventTitle).toBe("DXF parse run recorded");
    expect(payload?.nextSteps.steps[0].targetRoute).toBe("/workflow-board");
    expect(payload?.moduleLinks.links[0].module).toBe("cad_intake");
  });

  it("maps the health summary", async () => {
    mockFetchOnce({
      project_id: "proj_brookside_meadows",
      snapshot_id: "cc_1",
      overall_status: "needs_attention",
      current_review_cycle_id: "cycle_1",
      attention_count: 5,
      ready_for_handoff_count: 0,
      carry_forward_count: 2,
      needs_more_information_count: 1,
      cad_findings_count: 4,
      resubmittal_count: 1,
      open_follow_up_count: 1,
      response_mapping_gap_count: 2,
      revision_change_count: 3,
      readiness_ready_count: 4,
      summary: "summary",
      limitations_note: "does not approve",
    });
    const summary = await getProjectHealthSummary();
    expect(summary?.overallStatus).toBe("needs_attention");
    expect(summary?.readinessReadyCount).toBe(4);
  });

  it("filters attention items by status via query params", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    } as Response);
    globalThis.fetch = fetchSpy;
    await getReviewerAttentionItems({ status: "open", sourceModule: "cad_intake" });
    const url = fetchSpy.mock.calls[0][0] as string;
    expect(url).toContain("status=open");
    expect(url).toContain("source_module=cad_intake");
  });

  it("surfaces a backend error detail on an invalid attention status", async () => {
    mockFetchOnce({ detail: "Invalid attention item status 'approved'." }, false, 422);
    const result = await updateAttentionItemStatus("att_1", "approved");
    expect(result.ok).toBe(false);
    expect(result.error).toContain("Invalid attention item status");
  });

  it("reports the backend unreachable on a network failure", async () => {
    mockFetchUnreachable();
    const payload = await getProjectCommandCenter();
    expect(payload).toBeNull();

    const result = await generateCommandCenterSnapshot();
    expect(result.ok).toBe(false);
    expect(result.backendReachable).toBe(false);
  });
});
