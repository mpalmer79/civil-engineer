import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createReviewCycle,
  getResubmittalPackage,
  getReviewCycleDashboard,
  getReviewCycles,
  getRevisionChanges,
  runRevisionComparison,
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

describe("Phase 13 review cycle API mapping", () => {
  it("maps snake_case review cycles to camelCase", async () => {
    mockFetchOnce([
      {
        review_cycle_id: "cycle_1",
        project_id: "proj_brookside_meadows",
        cycle_number: 1,
        cycle_name: "Initial review",
        status: "active",
        started_at: "2026-06-25T00:00:00Z",
        completed_at: null,
        source_response_package_id: "rp_1",
        source_workflow_board_id: "proj_brookside_meadows",
        summary: "Review cycle 1.",
        requires_human_review: true,
        created_at: "2026-06-25T00:00:00Z",
        updated_at: "2026-06-25T00:00:00Z",
      },
    ]);
    const cycles = await getReviewCycles();
    expect(cycles).toHaveLength(1);
    expect(cycles[0].reviewCycleId).toBe("cycle_1");
    expect(cycles[0].cycleNumber).toBe(1);
    expect(cycles[0].requiresHumanReview).toBe(true);
  });

  it("maps the review cycle dashboard including nested cycles", async () => {
    mockFetchOnce({
      project_id: "proj_brookside_meadows",
      cycle_count: 2,
      active_cycle_id: "cycle_2",
      active_cycle_number: 2,
      review_cycles: [
        {
          review_cycle_id: "cycle_2",
          project_id: "proj_brookside_meadows",
          cycle_number: 2,
          cycle_name: "Review round 2",
          status: "active",
          started_at: "2026-06-25T00:00:00Z",
          completed_at: null,
          source_response_package_id: null,
          source_workflow_board_id: "proj_brookside_meadows",
          summary: "Round 2.",
          requires_human_review: true,
          created_at: "2026-06-25T00:00:00Z",
          updated_at: "2026-06-25T00:00:00Z",
        },
      ],
      resubmittal_count: 1,
      resubmittal_statuses: { received: 1 },
      applicant_response_count: 2,
      unmapped_response_count: 1,
      comparison_run_count: 1,
      revision_change_count: 30,
      carry_forward_count: 3,
      resolution_count: 2,
      resolution_statuses: { still_open: 1, addressed_for_review: 1 },
      open_item_count: 1,
      next_cycle_ready: true,
      limitations_note: "review support only",
    });
    const dashboard = await getReviewCycleDashboard();
    expect(dashboard?.cycleCount).toBe(2);
    expect(dashboard?.reviewCycles).toHaveLength(1);
    expect(dashboard?.reviewCycles[0].cycleName).toBe("Review round 2");
    expect(dashboard?.resolutionStatuses).toEqual({
      still_open: 1,
      addressed_for_review: 1,
    });
  });

  it("maps a resubmittal package with documents and responses", async () => {
    mockFetchOnce({
      resubmittal_package_id: "resub_1",
      project_id: "proj_brookside_meadows",
      review_cycle_id: "cycle_1",
      package_name: "Resubmittal 1",
      submitted_by: "Design Engineer",
      submitted_at: "2026-06-25T00:00:00Z",
      received_at: "2026-06-25T00:00:00Z",
      status: "received",
      summary: "received",
      reviewer_note: null,
      requires_human_review: true,
      created_at: "2026-06-25T00:00:00Z",
      updated_at: "2026-06-25T00:00:00Z",
      documents: [
        {
          resubmittal_document_id: "rd_1",
          project_id: "proj_brookside_meadows",
          review_cycle_id: "cycle_1",
          resubmittal_package_id: "resub_1",
          document_type: "dxf_cad_file",
          source_type: "cad_file",
          source_id: "cad_1",
          file_name: "site.dxf",
          description: "linked",
          status: "linked",
          created_at: "2026-06-25T00:00:00Z",
        },
      ],
      applicant_responses: [],
      note: "review support only",
    });
    const pkg = await getResubmittalPackage("resub_1");
    expect(pkg?.packageName).toBe("Resubmittal 1");
    expect(pkg?.documents).toHaveLength(1);
    expect(pkg?.documents?.[0].documentType).toBe("dxf_cad_file");
  });

  it("maps revision change records", async () => {
    mockFetchOnce([
      {
        change_record_id: "chg_1",
        project_id: "proj_brookside_meadows",
        review_cycle_id: "cycle_1",
        comparison_run_id: "rev_1",
        change_type: "added",
        source_category: "sheet_reference",
        previous_value: null,
        current_value: "C-8.8",
        normalized_key: "C-8.8",
        layer_name: null,
        reference_type: "sheet_reference",
        severity: "low",
        linked_cad_review_finding_id: null,
        linked_workflow_item_id: null,
        reviewer_status: "draft",
        reviewer_note: null,
        requires_human_review: true,
        created_at: "2026-06-25T00:00:00Z",
      },
    ]);
    const changes = await getRevisionChanges("rev_1");
    expect(changes[0].changeType).toBe("added");
    expect(changes[0].currentValue).toBe("C-8.8");
  });

  it("surfaces a backend error detail from a rejected comparison", async () => {
    mockFetchOnce({ detail: "Parse run not found." }, false, 404);
    const result = await runRevisionComparison("cycle_1", "a", "b");
    expect(result.ok).toBe(false);
    expect(result.error).toContain("Parse run not found");
  });

  it("reports the backend unreachable on a network failure", async () => {
    mockFetchUnreachable();
    const cycles = await getReviewCycles();
    expect(cycles).toEqual([]);

    const result = await createReviewCycle("Round 2");
    expect(result.ok).toBe(false);
    expect(result.backendReachable).toBe(false);
  });
});
