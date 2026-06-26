import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createDraftFindingFromChecklistItem,
  createProjectChecklistFromRulePack,
  listRulePacks,
  searchChecklistItemEvidence,
  updateProjectChecklistItem,
} from "@/lib/api";

function mockFetchOnce(payload: unknown, ok = true, status = 200) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  } as Response);
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("listRulePacks", () => {
  it("maps the snake_case rule pack payload", async () => {
    mockFetchOnce([
      {
        rule_pack_id: "rulepack_starter",
        name: "Starter Pack",
        jurisdiction_name: "Starter template",
        review_domain: "stormwater",
        version_label: "v1",
        source_mode: "seeded_demo",
        is_active: true,
        item_count: 16,
      },
    ]);
    const packs = await listRulePacks();
    expect(packs).toHaveLength(1);
    expect(packs?.[0].itemCount).toBe(16);
    expect(packs?.[0].sourceMode).toBe("seeded_demo");
  });
});

describe("createProjectChecklistFromRulePack", () => {
  it("sends the rule pack id and maps the checklist", async () => {
    mockFetchOnce({
      project_checklist_id: "pcl_1",
      project_id: "proj_1",
      rule_pack_id: "rulepack_starter",
      name: "Starter Pack",
      status: "checklist_started",
      source_mode: "user_created",
      item_count: 16,
      evidence_status_summary: { not_reviewed: 16 },
      review_status_summary: { not_started: 16 },
    });
    const result = await createProjectChecklistFromRulePack("proj_1", {
      rulePackId: "rulepack_starter",
    });
    expect(result.ok).toBe(true);
    expect(result.data?.itemCount).toBe(16);
    const body = JSON.parse(
      (
        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
          .calls[0][1] as RequestInit
      ).body as string,
    );
    expect(body.rule_pack_id).toBe("rulepack_starter");
  });
});

describe("updateProjectChecklistItem", () => {
  it("sends safe status values", async () => {
    mockFetchOnce({
      project_checklist_item_id: "pcli_1",
      project_checklist_id: "pcl_1",
      project_id: "proj_1",
      item_code: "SC-01",
      category: "Submission completeness",
      requirement_text: "A complete submission is provided.",
      expected_evidence: "Cover sheet and index.",
      applicability_status: "applies",
      evidence_status: "missing_evidence",
      review_status: "reviewer_note_added",
      risk_level: "medium",
    });
    const result = await updateProjectChecklistItem("proj_1", "pcli_1", {
      evidenceStatus: "missing_evidence",
      reviewerNote: "Request the drainage report",
    });
    expect(result.ok).toBe(true);
    expect(result.data?.evidenceStatus).toBe("missing_evidence");
    const body = JSON.parse(
      (
        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
          .calls[0][1] as RequestInit
      ).body as string,
    );
    expect(body.evidence_status).toBe("missing_evidence");
  });

  it("surfaces a rejected status error", async () => {
    mockFetchOnce({ detail: "Invalid evidence_status 'compliant'." }, false, 422);
    const result = await updateProjectChecklistItem("proj_1", "pcli_1", {
      evidenceStatus: "compliant",
    });
    expect(result.ok).toBe(false);
    expect(result.error).toContain("Invalid evidence_status");
  });
});

describe("searchChecklistItemEvidence", () => {
  it("maps the evidence search response", async () => {
    mockFetchOnce({
      project_id: "proj_1",
      query_text: "detention basin",
      query_type: "checklist_item",
      retrieval_query_id: "rq_1",
      result_count: 1,
      results: [
        {
          document_id: "doc_1",
          document_name: "Plan.pdf",
          page_number: 1,
          excerpt: "...detention basin...",
          match_terms: ["detention"],
          ranking_score: 0.8,
        },
      ],
      message: "1 retrieval candidate(s) for reviewer review.",
    });
    const result = await searchChecklistItemEvidence("proj_1", "pcli_1");
    expect(result.ok).toBe(true);
    expect(result.data?.resultCount).toBe(1);
    expect(result.data?.results[0].rankingScore).toBe(0.8);
  });
});

describe("createDraftFindingFromChecklistItem", () => {
  it("maps the draft finding result with a safe draft status", async () => {
    mockFetchOnce({
      finding: {
        finding_id: "find_checklist_1",
        project_id: "proj_1",
        title: "Detention basin outlet sizing",
        category: "Detention and outlet control",
        risk_level: "high",
        evidence_status: "missing_evidence",
        human_review_status: "draft",
        finding_origin: "checklist_review",
        source_mode: "user_created",
        related_checklist_items: ["pcli_1"],
      },
      citation: null,
      checklist_item: {
        project_checklist_item_id: "pcli_1",
        project_checklist_id: "pcl_1",
        project_id: "proj_1",
        item_code: "DO-01",
        category: "Detention and outlet control",
        requirement_text: "Detention storage and outlet control are sized.",
        expected_evidence: "Stage storage table.",
        applicability_status: "applies",
        evidence_status: "missing_evidence",
        review_status: "draft_finding_created",
        risk_level: "high",
        related_finding_id: "find_checklist_1",
      },
    });
    const result = await createDraftFindingFromChecklistItem(
      "proj_1",
      "pcli_1",
      { title: "Detention basin outlet sizing" },
    );
    expect(result.ok).toBe(true);
    expect(result.data?.finding.humanReviewStatus).toBe("draft");
    expect(result.data?.finding.findingOrigin).toBe("checklist_review");
    expect(result.data?.checklistItem.reviewStatus).toBe(
      "draft_finding_created",
    );
  });
});
