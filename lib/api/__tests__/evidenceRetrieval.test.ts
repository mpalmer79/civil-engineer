import { afterEach, describe, expect, it, vi } from "vitest";

import {
  dismissEvidenceCandidate,
  listProjectEvidenceCandidates,
  promoteCandidateToDraftFinding,
  saveEvidenceCandidate,
  searchProjectEvidence,
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

describe("searchProjectEvidence", () => {
  it("sends the expected snake_case payload and maps the response", async () => {
    mockFetchOnce({
      project_id: "proj_1",
      query_text: "detention basin",
      query_type: "keyword",
      retrieval_query_id: "rq_user_1",
      result_count: 1,
      results: [
        {
          document_id: "doc_1",
          document_name: "Plan Set.pdf",
          document_type: "stormwater_report",
          document_page_id: "docpage_1",
          page_number: 2,
          page_label: "Page 2",
          text_extraction_status: "text_extracted",
          excerpt: "...detention basin outlet...",
          match_terms: ["detention", "basin"],
          ranking_score: 0.82,
          ranking_reason: "Ranked by exact phrase appears on this page.",
          candidate_origin: "keyword_search",
          retrieval_query_id: "rq_user_1",
        },
      ],
      message: "1 retrieval candidate(s) for reviewer review.",
    });

    const result = await searchProjectEvidence("proj_1", {
      queryText: "detention basin",
      queryType: "keyword",
      filters: { documentType: "stormwater_report", pageMin: 1 },
      limit: 5,
    });

    expect(result.ok).toBe(true);
    expect(result.data?.resultCount).toBe(1);
    expect(result.data?.results[0].rankingScore).toBe(0.82);
    expect(result.data?.results[0].matchTerms).toEqual(["detention", "basin"]);

    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    expect(call[0]).toContain(
      "/api/v1/projects/proj_1/evidence-retrieval/search",
    );
    const body = JSON.parse((call[1] as RequestInit).body as string);
    expect(body.query_text).toBe("detention basin");
    expect(body.query_type).toBe("keyword");
    expect(body.filters.document_type).toBe("stormwater_report");
    expect(body.filters.page_min).toBe(1);
    expect(body.limit).toBe(5);
  });

  it("surfaces a backend error detail", async () => {
    mockFetchOnce({ detail: "query_text is required." }, false, 422);
    const result = await searchProjectEvidence("proj_1", {
      queryText: "x",
    });
    expect(result.ok).toBe(false);
    expect(result.error).toBe("query_text is required.");
  });

  it("reports an unreachable backend", async () => {
    mockFetchUnreachable();
    const result = await searchProjectEvidence("proj_1", {
      queryText: "detention basin",
    });
    expect(result.ok).toBe(false);
    expect(result.backendReachable).toBe(false);
  });
});

describe("evidence candidate client", () => {
  it("saves a candidate with a safe default origin", async () => {
    mockFetchOnce({
      evidence_candidate_id: "cand_1",
      project_id: "proj_1",
      document_id: "doc_1",
      candidate_title: "Plan Set.pdf page 2",
      candidate_status: "saved_for_review",
      candidate_origin: "manual_save",
      match_terms: [],
      ranking_score: 0,
    });
    const result = await saveEvidenceCandidate("proj_1", {
      documentId: "doc_1",
      candidateTitle: "Plan Set.pdf page 2",
    });
    expect(result.ok).toBe(true);
    expect(result.data?.candidateStatus).toBe("saved_for_review");
    const body = JSON.parse(
      (
        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
          .calls[0][1] as RequestInit
      ).body as string,
    );
    expect(body.candidate_origin).toBe("manual_save");
  });

  it("lists candidates filtered by status", async () => {
    mockFetchOnce([
      {
        evidence_candidate_id: "cand_1",
        project_id: "proj_1",
        document_id: "doc_1",
        candidate_title: "Plan Set.pdf page 2",
        candidate_status: "saved_for_review",
        candidate_origin: "manual_save",
        match_terms: [],
        ranking_score: 0,
      },
    ]);
    const list = await listProjectEvidenceCandidates("proj_1", {
      candidateStatus: "saved_for_review",
    });
    expect(list).toHaveLength(1);
    const url = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0][0] as string;
    expect(url).toContain("candidate_status=saved_for_review");
  });

  it("dismisses a candidate", async () => {
    mockFetchOnce({
      evidence_candidate_id: "cand_1",
      project_id: "proj_1",
      document_id: "doc_1",
      candidate_title: "Plan Set.pdf page 2",
      candidate_status: "dismissed_by_reviewer",
      candidate_origin: "manual_save",
      match_terms: [],
      ranking_score: 0,
    });
    const result = await dismissEvidenceCandidate("proj_1", "cand_1", "n/a");
    expect(result.ok).toBe(true);
    expect(result.data?.candidateStatus).toBe("dismissed_by_reviewer");
  });

  it("promotes a candidate and maps the draft finding", async () => {
    mockFetchOnce({
      finding: {
        finding_id: "find_draft_1",
        project_id: "proj_1",
        title: "Outlet sizing draft",
        category: "stormwater",
        risk_level: "medium",
        evidence_status: "needs_reviewer_confirmation",
        human_review_status: "draft",
        finding_origin: "retrieval_candidate",
        source_mode: "user_created",
        created_by_name: "Demo Reviewer",
      },
      citation: {
        evidence_citation_id: "cite_1",
        project_id: "proj_1",
        finding_id: "find_draft_1",
        document_id: "doc_1",
        document_page_id: "docpage_1",
        page_number: 2,
        citation_type: "reviewer_selected",
        citation_status: "needs_reviewer_confirmation",
      },
      candidate: {
        evidence_candidate_id: "cand_1",
        project_id: "proj_1",
        document_id: "doc_1",
        candidate_title: "Plan Set.pdf page 2",
        candidate_status: "promoted_to_draft",
        candidate_origin: "manual_save",
        match_terms: [],
        ranking_score: 0,
        promoted_finding_id: "find_draft_1",
      },
    });
    const result = await promoteCandidateToDraftFinding("proj_1", "cand_1", {
      title: "Outlet sizing draft",
      riskLevel: "medium",
    });
    expect(result.ok).toBe(true);
    expect(result.data?.finding.humanReviewStatus).toBe("draft");
    expect(result.data?.finding.findingOrigin).toBe("retrieval_candidate");
    expect(result.data?.candidate.candidateStatus).toBe("promoted_to_draft");
  });
});
