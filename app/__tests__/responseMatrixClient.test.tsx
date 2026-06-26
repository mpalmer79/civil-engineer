import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  carryForwardMatrixItem,
  createResponseMatrix,
  getResponseMatrix,
  listResponseMatrices,
  recordApplicantResponse,
} from "@/lib/api/responseMatrix";
import {
  carryForwardItemsToRound,
  getResubmittalRoundSummary,
  listResubmittalRounds,
  registerResubmittalRound,
} from "@/lib/api/resubmittals";

// Sprint 7 client tests. These exercise the snake_case to camelCase mapping and
// the request payloads. Applicant responses are recorded for reviewer review,
// never as proof. Carry-forward means continued review, not resolution.

const rawMatrix = {
  response_matrix_id: "rm_1",
  project_id: "proj_1",
  name: "Response matrix 1",
  current_round_number: 1,
  status: "matrix_started",
  source_mode: "user_created",
  created_by_name: "Demo Reviewer",
  created_at: null,
  updated_at: null,
  item_count: 2,
  applicant_response_summary: { awaiting_applicant_response: 2 },
  reviewer_follow_up_summary: { not_reviewed: 2 },
  carry_forward_summary: { not_carried_forward: 2 },
};

const rawItem = {
  response_matrix_item_id: "rmi_1",
  response_matrix_id: "rm_1",
  project_id: "proj_1",
  source_finding_id: "find_1",
  source_checklist_item_id: null,
  item_number: "R1-001",
  category: "Detention and outlet control",
  reviewer_comment_draft: "Provide stage storage table.",
  requested_evidence: null,
  applicant_response_text: null,
  applicant_response_status: "awaiting_applicant_response",
  reviewer_follow_up_status: "not_reviewed",
  carry_forward_status: "not_carried_forward",
  current_round_number: 1,
  carried_from_round_number: null,
  carried_to_round_number: null,
  related_document_ids: [],
  related_citation_ids: [],
  reviewer_note: null,
  created_by_name: "Demo Reviewer",
  updated_by_name: null,
  sort_order: 0,
  created_at: null,
  updated_at: null,
};

const rawRound = {
  resubmittal_round_id: "rr_1",
  project_id: "proj_1",
  response_matrix_id: "rm_1",
  round_number: 2,
  round_label: "First resubmittal",
  received_at: null,
  submitted_by_name: "Design firm",
  submitted_by_organization: null,
  status: "round_registered",
  summary: null,
  document_ids: ["doc_1"],
  carried_forward_item_ids: ["rmi_1"],
  document_count: 1,
  carried_forward_item_count: 1,
  created_by_name: "Demo Reviewer",
  created_at: null,
  updated_at: null,
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

describe("response matrix client", () => {
  it("maps a list of matrices to camelCase", async () => {
    vi.stubGlobal("fetch", mockFetchOnce([rawMatrix]));
    const result = await listResponseMatrices("proj_1");
    expect(result).not.toBeNull();
    expect(result?.[0].responseMatrixId).toBe("rm_1");
    expect(result?.[0].applicantResponseSummary.awaiting_applicant_response).toBe(
      2,
    );
  });

  it("returns null when the backend is unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("network");
      }) as unknown as typeof fetch,
    );
    const result = await listResponseMatrices("proj_1");
    expect(result).toBeNull();
  });

  it("maps a single matrix on get", async () => {
    vi.stubGlobal("fetch", mockFetchOnce(rawMatrix));
    const result = await getResponseMatrix("proj_1", "rm_1");
    expect(result?.name).toBe("Response matrix 1");
  });

  it("sends a create payload and maps the response", async () => {
    const fetchMock = mockFetchOnce(rawMatrix);
    vi.stubGlobal("fetch", fetchMock);
    const result = await createResponseMatrix("proj_1", { name: "My matrix" });
    expect(result.ok).toBe(true);
    expect(result.data?.responseMatrixId).toBe("rm_1");
    const call = (fetchMock as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const body = JSON.parse((call[1] as { body: string }).body);
    expect(body.name).toBe("My matrix");
  });

  it("records an applicant response with text in the payload", async () => {
    const fetchMock = mockFetchOnce({
      ...rawItem,
      applicant_response_text: "We added the table.",
      applicant_response_status: "applicant_response_received",
      reviewer_follow_up_status: "needs_reviewer_confirmation",
    });
    vi.stubGlobal("fetch", fetchMock);
    const result = await recordApplicantResponse("proj_1", "rmi_1", {
      applicantResponseText: "We added the table.",
    });
    expect(result.ok).toBe(true);
    expect(result.data?.applicantResponseStatus).toBe(
      "applicant_response_received",
    );
    const call = (fetchMock as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const body = JSON.parse((call[1] as { body: string }).body);
    expect(body.applicant_response_text).toBe("We added the table.");
  });

  it("carries an item forward with a safe status payload", async () => {
    const fetchMock = mockFetchOnce({
      ...rawItem,
      carry_forward_status: "carried_forward_for_review",
      carried_to_round_number: 2,
    });
    vi.stubGlobal("fetch", fetchMock);
    const result = await carryForwardMatrixItem("proj_1", "rmi_1", {
      carryForwardStatus: "carried_forward_for_review",
    });
    expect(result.ok).toBe(true);
    expect(result.data?.carryForwardStatus).toBe("carried_forward_for_review");
    expect(result.data?.carriedToRoundNumber).toBe(2);
  });

  it("surfaces a backend error detail on a failed mutation", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({ detail: "Reviewer access required." }, false, 403),
    );
    const result = await createResponseMatrix("proj_1");
    expect(result.ok).toBe(false);
    expect(result.error).toBe("Reviewer access required.");
  });
});

describe("resubmittal client", () => {
  it("maps a list of rounds to camelCase", async () => {
    vi.stubGlobal("fetch", mockFetchOnce([rawRound]));
    const result = await listResubmittalRounds("proj_1");
    expect(result?.[0].resubmittalRoundId).toBe("rr_1");
    expect(result?.[0].roundNumber).toBe(2);
    expect(result?.[0].documentCount).toBe(1);
  });

  it("registers a round with the expected payload", async () => {
    const fetchMock = mockFetchOnce(rawRound);
    vi.stubGlobal("fetch", fetchMock);
    const result = await registerResubmittalRound("proj_1", {
      roundLabel: "First resubmittal",
      submittedByName: "Design firm",
    });
    expect(result.ok).toBe(true);
    const call = (fetchMock as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const body = JSON.parse((call[1] as { body: string }).body);
    expect(body.round_label).toBe("First resubmittal");
    expect(body.submitted_by_name).toBe("Design firm");
  });

  it("carries items into a round with matrix item ids", async () => {
    const fetchMock = mockFetchOnce(rawRound);
    vi.stubGlobal("fetch", fetchMock);
    const result = await carryForwardItemsToRound("proj_1", "rr_1", {
      matrixItemIds: ["rmi_1"],
    });
    expect(result.ok).toBe(true);
    const call = (fetchMock as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const body = JSON.parse((call[1] as { body: string }).body);
    expect(body.matrix_item_ids).toEqual(["rmi_1"]);
  });

  it("maps a round summary", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({
        resubmittal_round_id: "rr_1",
        project_id: "proj_1",
        round_number: 2,
        status: "documents_received",
        document_count: 1,
        carried_forward_item_count: 1,
        matrix_item_count: 1,
        applicant_response_summary: { applicant_response_received: 1 },
        carry_forward_summary: { carried_forward_for_review: 1 },
      }),
    );
    const result = await getResubmittalRoundSummary("proj_1", "rr_1");
    expect(result?.matrixItemCount).toBe(1);
    expect(result?.applicantResponseSummary.applicant_response_received).toBe(1);
  });
});
