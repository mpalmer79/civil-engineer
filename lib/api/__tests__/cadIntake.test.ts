import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createCadFileRecord,
  getCadFiles,
  getCadParseSummary,
  getCadReviewFindings,
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

describe("CAD intake API mapping", () => {
  it("maps a snake_case CAD file list to the camelCase shape", async () => {
    mockFetchOnce([
      {
        cad_file_id: "cad_1",
        project_id: "proj_brookside_meadows",
        file_name: "brookside_meadows.dxf",
        file_type: "dxf",
        file_size_bytes: 19796,
        storage_path: "/app/cad_samples/brookside_meadows.dxf",
        upload_status: "parsed",
        uploaded_by: "Town Engineer",
        limitations_note: "DXF metadata extraction for review support only.",
        created_at: "2026-06-24T00:00:00Z",
      },
    ]);

    const files = await getCadFiles();
    expect(files).toHaveLength(1);
    expect(files[0].cadFileId).toBe("cad_1");
    expect(files[0].fileType).toBe("dxf");
    expect(files[0].uploadStatus).toBe("parsed");
  });

  it("maps the parse summary, including nested record fields", async () => {
    mockFetchOnce({
      parse_run_id: "cadrun_1",
      cad_file_id: "cad_1",
      project_id: "proj_brookside_meadows",
      status: "completed",
      entity_count: 23,
      layer_count: 10,
      block_count: 1,
      text_count: 18,
      warning_count: 0,
      reference_candidate_count: 13,
      finding_count: 4,
      layers_by_category: { stormwater: 1, unknown: 3 },
      references_by_type: { sheet_reference: 3 },
      references_by_confidence: { high: 3, needs_human_review: 2 },
      findings_by_type: { missing_plan_sheet_match: 1 },
      limitations_note: "DXF metadata extraction for review support only.",
    });

    const summary = await getCadParseSummary("cadrun_1");
    expect(summary).not.toBeNull();
    expect(summary?.entityCount).toBe(23);
    expect(summary?.referencesByConfidence).toEqual({
      high: 3,
      needs_human_review: 2,
    });
    expect(summary?.findingsByType).toEqual({ missing_plan_sheet_match: 1 });
  });

  it("maps CAD review findings", async () => {
    mockFetchOnce([
      {
        cad_review_finding_id: "cadfind_1",
        parse_run_id: "cadrun_1",
        cad_file_id: "cad_1",
        project_id: "proj_brookside_meadows",
        finding_type: "missing_plan_sheet_match",
        title: "Referenced sheet C-9.9 has no plan sheet match",
        description: "The DXF references sheet C-9.9.",
        severity: "medium",
        source_reference_candidate_id: "cadref_1",
        source_layer_extract_id: null,
        source_text_extract_id: "cadtxt_1",
        linked_plan_sheet_id: null,
        linked_workflow_item_id: null,
        status: "draft",
        requires_human_review: true,
        created_at: "2026-06-24T00:00:00Z",
      },
    ]);

    const findings = await getCadReviewFindings();
    expect(findings[0].findingType).toBe("missing_plan_sheet_match");
    expect(findings[0].status).toBe("draft");
    expect(findings[0].requiresHumanReview).toBe(true);
  });

  it("surfaces a backend error detail when registering an unknown sample", async () => {
    mockFetchOnce({ detail: "Unknown sample DXF 'nope'." }, false, 404);
    const result = await createCadFileRecord("nope");
    expect(result.ok).toBe(false);
    expect(result.error).toContain("Unknown sample");
  });

  it("reports the backend unreachable on a network failure", async () => {
    mockFetchUnreachable();
    const files = await getCadFiles();
    expect(files).toEqual([]);

    const result = await createCadFileRecord();
    expect(result.ok).toBe(false);
    expect(result.backendReachable).toBe(false);
  });
});
