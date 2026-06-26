import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  addFindingsToPackage,
  createPackageRevision,
  createResponsePackage,
  issueResponsePackage,
  listResponsePackages,
  previewResponsePackage,
  updateResponsePackageItem,
} from "@/lib/api/reviewerResponsePackages";
import {
  generateCommentLetterDraft,
  previewCommentLetter,
  updateCommentLetterDraft,
} from "@/lib/api/commentLetters";

// Sprint 8 client tests. These exercise the snake_case to camelCase mapping and
// the request payloads. Package issuance records a reviewer communication only.

const rawPackage = {
  response_package_id: "rpkg_1",
  project_id: "proj_1",
  response_matrix_id: null,
  resubmittal_round_id: null,
  package_title: "Initial review comments",
  package_number: 1,
  revision_number: 0,
  status: "package_draft",
  package_type: "initial_review_comment_letter",
  source_mode: "user_created",
  prepared_by_name: "Demo Reviewer",
  issued_by_name: null,
  issued_at: null,
  created_at: null,
  updated_at: null,
  item_count: 0,
  included_item_count: 0,
  items: [],
};

const rawItem = {
  response_package_item_id: "rpi_1",
  response_package_id: "rpkg_1",
  project_id: "proj_1",
  source_type: "finding",
  reviewer_comment_text: "Provide the outlet detail.",
  include_in_letter: true,
  sort_order: 0,
  item_status: "item_draft",
};

const rawDraft = {
  comment_letter_draft_id: "cldraft_1",
  response_package_id: "rpkg_1",
  project_id: "proj_1",
  title: "Comment letter draft",
  subject_line: "Stormwater review comments: Brookside Meadows",
  introduction_text: "Intro",
  comment_items_text: "Comment 1",
  closing_text: "Closing",
  status: "draft_created",
  revision_number: 0,
  boundary_statement: "This draft is prepared for reviewer support. It does not approve plans.",
};

function mockFetchOnce(body: unknown, ok = true, status = 200) {
  return vi.fn(async () => ({
    ok,
    status,
    json: async () => body,
  })) as unknown as typeof fetch;
}

beforeEach(() => {
  vi.unstubAllGlobals();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("response package client", () => {
  it("maps a list of packages to camelCase", async () => {
    vi.stubGlobal("fetch", mockFetchOnce([rawPackage]));
    const result = await listResponsePackages("proj_1");
    expect(result?.[0].responsePackageId).toBe("rpkg_1");
    expect(result?.[0].packageType).toBe("initial_review_comment_letter");
  });

  it("returns null when the backend is unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("network");
      }) as unknown as typeof fetch,
    );
    expect(await listResponsePackages("proj_1")).toBeNull();
  });

  it("sends a create payload and maps the response", async () => {
    const fetchMock = mockFetchOnce(rawPackage);
    vi.stubGlobal("fetch", fetchMock);
    const result = await createResponsePackage("proj_1", {
      packageTitle: "Initial",
      packageType: "initial_review_comment_letter",
    });
    expect(result.ok).toBe(true);
    const call = (fetchMock as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    const body = JSON.parse((call[1] as { body: string }).body);
    expect(body.package_title).toBe("Initial");
    expect(body.package_type).toBe("initial_review_comment_letter");
  });

  it("adds findings with the finding ids in the payload", async () => {
    const fetchMock = mockFetchOnce({ ...rawPackage, item_count: 1 });
    vi.stubGlobal("fetch", fetchMock);
    const result = await addFindingsToPackage("proj_1", "rpkg_1", ["find_1"]);
    expect(result.ok).toBe(true);
    const call = (fetchMock as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    const body = JSON.parse((call[1] as { body: string }).body);
    expect(body.finding_ids).toEqual(["find_1"]);
  });

  it("updates a package item with a PATCH and safe status", async () => {
    const fetchMock = mockFetchOnce({
      ...rawItem,
      include_in_letter: false,
      item_status: "needs_reviewer_confirmation",
    });
    vi.stubGlobal("fetch", fetchMock);
    const result = await updateResponsePackageItem("proj_1", "rpi_1", {
      includeInLetter: false,
      itemStatus: "needs_reviewer_confirmation",
    });
    expect(result.ok).toBe(true);
    expect(result.data?.includeInLetter).toBe(false);
    const call = (fetchMock as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect((call[1] as { method: string }).method).toBe("PATCH");
  });

  it("maps a package preview with the boundary statement", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({
        response_package_id: "rpkg_1",
        project_id: "proj_1",
        project_name: "Brookside Meadows",
        package_title: "Initial review comments",
        package_type: "initial_review_comment_letter",
        package_number: 1,
        revision_number: 0,
        status: "package_in_review",
        boundary_statement: "This response package is prepared for reviewer support. It does not approve plans.",
        item_count: 1,
        items: [
          {
            item_number: "1",
            category: "stormwater",
            reviewer_comment_text: "Provide the outlet detail.",
            item_status: "item_draft",
          },
        ],
      }),
    );
    const preview = await previewResponsePackage("proj_1", "rpkg_1");
    expect(preview?.boundaryStatement.toLowerCase()).toContain("does not approve");
    expect(preview?.items[0].reviewerCommentText).toBe("Provide the outlet detail.");
  });

  it("issues a package and maps the issued record", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({
        ...rawPackage,
        status: "issued_by_reviewer",
        issued_by_name: "Demo Reviewer",
        issued_at: "2026-06-26T00:00:00Z",
      }),
    );
    const result = await issueResponsePackage("proj_1", "rpkg_1");
    expect(result.ok).toBe(true);
    expect(result.data?.status).toBe("issued_by_reviewer");
  });

  it("creates a revision with a safe status", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({ ...rawPackage, status: "revision_started", revision_number: 1 }),
    );
    const result = await createPackageRevision("proj_1", "rpkg_1", {
      revisionReason: "Applicant submitted revised plans.",
    });
    expect(result.data?.status).toBe("revision_started");
    expect(result.data?.revisionNumber).toBe(1);
  });

  it("surfaces a backend error detail on a failed mutation", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({ detail: "Reviewer access required." }, false, 403),
    );
    const result = await createResponsePackage("proj_1");
    expect(result.ok).toBe(false);
    expect(result.error).toBe("Reviewer access required.");
  });
});

describe("comment letter client", () => {
  it("generates a draft with the recipient payload", async () => {
    const fetchMock = mockFetchOnce(rawDraft);
    vi.stubGlobal("fetch", fetchMock);
    const result = await generateCommentLetterDraft("proj_1", "rpkg_1", {
      recipientName: "Design Firm",
    });
    expect(result.ok).toBe(true);
    expect(result.data?.boundaryStatement.toLowerCase()).toContain(
      "does not approve",
    );
    const call = (fetchMock as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    const body = JSON.parse((call[1] as { body: string }).body);
    expect(body.recipient_name).toBe("Design Firm");
  });

  it("updates a draft with a PATCH", async () => {
    const fetchMock = mockFetchOnce({ ...rawDraft, status: "reviewer_editing" });
    vi.stubGlobal("fetch", fetchMock);
    const result = await updateCommentLetterDraft("proj_1", "cldraft_1", {
      introductionText: "Updated intro.",
    });
    expect(result.ok).toBe(true);
    const call = (fetchMock as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect((call[1] as { method: string }).method).toBe("PATCH");
  });

  it("maps a comment letter preview", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({
        comment_letter_draft_id: "cldraft_1",
        response_package_id: "rpkg_1",
        project_id: "proj_1",
        title: "Comment letter draft",
        status: "draft_created",
        revision_number: 0,
        boundary_statement: "This draft is prepared for reviewer support. It does not approve plans.",
        sections: [{ heading: "Introduction", body: "Intro" }],
      }),
    );
    const preview = await previewCommentLetter("proj_1", "cldraft_1");
    expect(preview?.sections[0].heading).toBe("Introduction");
  });
});
