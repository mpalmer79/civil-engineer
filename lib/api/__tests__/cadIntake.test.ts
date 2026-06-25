import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createCadFileRecord,
  getCadFiles,
  getCadIntakeDashboard,
  getCadParseQueue,
  getCadParseSummary,
  getCadReviewFindings,
  getCadUploadLimits,
  getUnpromotedCadFindings,
  promoteCadFindingToWorkflow,
  promoteSelectedCadFindingsToWorkflow,
  uploadCadFile,
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

describe("Phase 12 CAD upload, queue, dashboard, and promotion", () => {
  it("maps the DXF upload limits", async () => {
    mockFetchOnce({
      supported_extensions: [".dxf"],
      supported_file_types: ["dxf"],
      max_file_size_bytes: 5000000,
      max_file_size_mb: 5,
      allowed_validation_statuses: ["accepted", "needs_human_review", "rejected"],
      allowed_queue_statuses: ["queued", "parsing", "completed"],
      note: "DXF is the only supported file type.",
    });
    const limits = await getCadUploadLimits();
    expect(limits?.supportedExtensions).toEqual([".dxf"]);
    expect(limits?.maxFileSizeMb).toBe(5);
    expect(limits?.allowedValidationStatuses).toContain("needs_human_review");
  });

  it("rejects a non-dxf file on the client before sending", async () => {
    const fetchSpy = vi.fn();
    globalThis.fetch = fetchSpy;
    const file = new File(["data"], "drawing.dwg", {
      type: "application/octet-stream",
    });
    const result = await uploadCadFile(file);
    expect(result.ok).toBe(false);
    expect(result.validationStatus).toBe("rejected");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("maps a successful DXF upload response", async () => {
    mockFetchOnce({
      cad_file: {
        cad_file_id: "cad_99",
        project_id: "proj_brookside_meadows",
        file_name: "site.dxf",
        file_type: "dxf",
        file_size_bytes: 1234,
        storage_path: "/uploads/proj/cad_abc.dxf",
        upload_status: "uploaded",
        uploaded_by: "reviewer",
        limitations_note: "review support only",
        original_file_name: "site.dxf",
        stored_file_name: "cad_abc.dxf",
        content_type: "application/dxf",
        upload_source: "browser_upload",
        validation_status: "accepted",
        validation_message: "DXF upload accepted for review-support parsing.",
        max_file_size_bytes: 5000000,
        parse_requested_at: null,
        parse_completed_at: null,
        created_at: "2026-06-25T00:00:00Z",
      },
      validation_status: "accepted",
      validation_message: "DXF upload accepted for review-support parsing.",
      next_action: "request_parse",
      note: "DXF stored for review-support parsing only.",
    });
    const file = new File(["0\nSECTION\nEOF\n"], "site.dxf", {
      type: "application/dxf",
    });
    const result = await uploadCadFile(file, "Town Engineer");
    expect(result.ok).toBe(true);
    expect(result.cadFile?.cadFileId).toBe("cad_99");
    expect(result.cadFile?.uploadSource).toBe("browser_upload");
    expect(result.validationStatus).toBe("accepted");
    expect(result.nextAction).toBe("request_parse");
  });

  it("surfaces a rejected upload detail from the backend", async () => {
    mockFetchOnce(
      { detail: "The uploaded file is empty (zero bytes)." },
      false,
      422,
    );
    const file = new File([""], "empty.dxf", { type: "application/dxf" });
    const result = await uploadCadFile(file);
    expect(result.ok).toBe(false);
    expect(result.error).toContain("empty");
  });

  it("maps the parse queue", async () => {
    mockFetchOnce([
      {
        cad_file_id: "cad_1",
        project_id: "proj_brookside_meadows",
        file_name: "site.dxf",
        upload_source: "browser_upload",
        upload_status: "parsed",
        validation_status: "accepted",
        validation_message: "ok",
        queue_status: "completed",
        parse_run_id: "cadrun_1",
        parse_status: "completed",
        warning_count: 0,
        error_message: null,
        finding_count: 3,
        parse_requested_at: "2026-06-25T00:00:00Z",
        parse_completed_at: "2026-06-25T00:00:01Z",
        requires_human_review: false,
      },
    ]);
    const queue = await getCadParseQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].queueStatus).toBe("completed");
    expect(queue[0].findingCount).toBe(3);
  });

  it("maps the CAD intake dashboard", async () => {
    mockFetchOnce({
      project_id: "proj_brookside_meadows",
      total_files: 2,
      files_needing_parse: 1,
      files_with_parse_failures: 1,
      parse_runs_needing_human_review: 1,
      total_findings: 5,
      unpromoted_findings_count: 4,
      promoted_findings_count: 1,
      queue_status_counts: { completed: 1, failed: 1 },
      validation_status_counts: { accepted: 2 },
      parse_status_counts: { completed: 1, failed: 1 },
      limitations_note: "review support only",
    });
    const dashboard = await getCadIntakeDashboard();
    expect(dashboard?.totalFiles).toBe(2);
    expect(dashboard?.unpromotedFindingsCount).toBe(4);
    expect(dashboard?.queueStatusCounts).toEqual({ completed: 1, failed: 1 });
  });

  it("maps unpromoted CAD findings", async () => {
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
        promoted_to_workflow: false,
        promoted_workflow_item_id: null,
        status: "draft",
        requires_human_review: true,
        created_at: "2026-06-25T00:00:00Z",
      },
    ]);
    const findings = await getUnpromotedCadFindings();
    expect(findings[0].promotedToWorkflow).toBe(false);
    expect(findings[0].linkedWorkflowItemId).toBeNull();
  });

  it("promotes a single CAD finding to workflow", async () => {
    mockFetchOnce({
      cad_review_finding_id: "cadfind_1",
      workflow_item_id: "wfi_1",
      created: true,
      already_promoted: false,
      note: "Workflow item created from CAD review finding.",
    });
    const result = await promoteCadFindingToWorkflow(
      "cadfind_1",
      "Town Engineer",
      "track this",
    );
    expect(result.ok).toBe(true);
    expect(result.created).toBe(true);
    expect(result.workflowItemId).toBe("wfi_1");
  });

  it("promotes selected CAD findings to workflow", async () => {
    mockFetchOnce({
      project_id: "proj_brookside_meadows",
      requested_count: 2,
      created_count: 2,
      already_promoted_count: 0,
      not_found_count: 0,
      workflow_item_ids: ["wfi_1", "wfi_2"],
      note: "Selected CAD findings promoted to workflow items.",
    });
    const result = await promoteSelectedCadFindingsToWorkflow(
      ["cadfind_1", "cadfind_2"],
      "Town Engineer",
    );
    expect(result.ok).toBe(true);
    expect(result.createdCount).toBe(2);
    expect(result.workflowItemIds).toEqual(["wfi_1", "wfi_2"]);
  });
});
