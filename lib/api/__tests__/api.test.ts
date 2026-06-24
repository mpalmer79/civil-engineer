import { afterEach, describe, expect, it, vi } from "vitest";

import { documents as staticDocuments } from "@/data/documents";
import {
  getDocuments,
  getReviewPacketSummary,
} from "@/lib/api";

function mockFetchOnce(payload: unknown, ok = true) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    json: async () => payload,
  } as Response);
}

function mockFetchUnreachable() {
  globalThis.fetch = vi.fn().mockRejectedValue(new Error("backend down"));
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("API mapping", () => {
  it("maps a snake_case document payload to the camelCase component shape", async () => {
    mockFetchOnce([
      {
        document_id: "doc_test",
        file_name: "test.pdf",
        document_type: "report",
        status: "present",
        purpose: "Test purpose",
        expected_key_information: "Key info",
        intentionally_missing_or_conflicting_information: "A known issue",
      },
    ]);

    const result = await getDocuments();

    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({
      documentId: "doc_test",
      fileName: "test.pdf",
      documentType: "report",
      status: "present",
      purpose: "Test purpose",
      expectedKeyInformation: "Key info",
      knownIssue: "A known issue",
    });
  });

  it("maps the snake_case review packet summary, including nested record fields", async () => {
    mockFetchOnce({
      packet_id: "packet_1",
      project_id: "proj_brookside_meadows",
      status: "draft",
      total_sections: 8,
      total_items: 54,
      total_evidence_links: 154,
      items_by_section_type: { plan_consistency: 6 },
      items_by_status: { draft: 54 },
      items_by_severity: { high: 10 },
      items_requiring_human_review: 50,
    });

    const summary = await getReviewPacketSummary("packet_1");

    expect(summary).not.toBeNull();
    expect(summary?.packetId).toBe("packet_1");
    expect(summary?.totalSections).toBe(8);
    expect(summary?.itemsBySectionType).toEqual({ plan_consistency: 6 });
    expect(summary?.itemsRequiringHumanReview).toBe(50);
  });
});

describe("Fallback path", () => {
  it("returns static seed data when the backend is unreachable", async () => {
    mockFetchUnreachable();

    const result = await getDocuments();

    expect(result).toEqual(staticDocuments);
    expect(result.length).toBeGreaterThan(0);
  });

  it("returns mapped backend data when the backend responds", async () => {
    mockFetchOnce([
      {
        document_id: "doc_backend",
        file_name: "backend.pdf",
        document_type: "report",
        status: "present",
        purpose: "From backend",
        expected_key_information: "Info",
        intentionally_missing_or_conflicting_information: null,
      },
    ]);

    const result = await getDocuments();

    expect(result).toHaveLength(1);
    expect(result[0].documentId).toBe("doc_backend");
    expect(result).not.toEqual(staticDocuments);
  });

  it("returns null for a packet summary when the backend is unreachable", async () => {
    mockFetchUnreachable();

    const summary = await getReviewPacketSummary("packet_1");

    expect(summary).toBeNull();
  });
});
