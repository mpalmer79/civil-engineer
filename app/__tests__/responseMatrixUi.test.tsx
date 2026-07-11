import { ok } from "@/lib/api/__tests__/testHelpers";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const refreshMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: refreshMock }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

// Final-outcome wording that must never appear in the Sprint 7 UI. The matrix is
// review-support only; applicant responses are recorded for reviewer review.
const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "compliant",
  "noncompliant",
  "passed review",
  "failed review",
  "verified",
  "validated",
  "resolved",
  "closed",
];

// Sensitive values that must never be rendered to the browser.
const FORBIDDEN_LEAKS = [
  "storage_path",
  "storage_key",
  "secret",
  "password",
  "token",
  "/var/",
];

const project = {
  projectId: "proj_1",
  projectName: "Brookside Meadows",
  projectType: "Subdivision",
  locationContext: "",
  jurisdiction: "Town",
  reviewType: "Review",
  reviewDomain: "stormwater",
  acreage: 1,
  disturbedArea: 1,
  proposedLots: 0,
  status: "intake_started",
  summary: "",
  sourceMode: "demo_fixture",
  createdByName: "Seeded demo",
  applicantName: null,
  applicantOrganization: null,
  designEngineerName: null,
  designFirm: null,
  submissionReference: null,
  reviewRoundCurrent: 1,
  parcelIds: [],
  createdAt: null,
  updatedAt: null,
  documentCount: 1,
  findingCount: 1,
  auditEventCount: 1,
};

const matrix = {
  responseMatrixId: "rm_1",
  projectId: "proj_1",
  name: "Brookside response matrix",
  currentRoundNumber: 1,
  status: "matrix_started",
  sourceMode: "user_created",
  createdByName: "Demo Reviewer",
  createdAt: null,
  updatedAt: null,
  itemCount: 1,
  applicantResponseSummary: { awaiting_applicant_response: 1 },
  reviewerFollowUpSummary: { not_reviewed: 1 },
  carryForwardSummary: { not_carried_forward: 1 },
};

const item = {
  responseMatrixItemId: "rmi_1",
  responseMatrixId: "rm_1",
  projectId: "proj_1",
  sourceFindingId: "find_1",
  sourceChecklistItemId: null,
  itemNumber: "R1-001",
  category: "Detention and outlet control",
  reviewerCommentDraft: "Provide a stage storage table.",
  requestedEvidence: "Stage storage computations.",
  applicantResponseText: null,
  applicantResponseStatus: "awaiting_applicant_response",
  reviewerFollowUpStatus: "not_reviewed",
  carryForwardStatus: "not_carried_forward",
  currentRoundNumber: 1,
  carriedFromRoundNumber: null,
  carriedToRoundNumber: null,
  relatedDocumentIds: [],
  relatedCitationIds: [],
  reviewerNote: null,
  createdByName: "Demo Reviewer",
  updatedByName: null,
  sortOrder: 0,
  createdAt: null,
  updatedAt: null,
};

const round = {
  resubmittalRoundId: "rr_1",
  projectId: "proj_1",
  responseMatrixId: "rm_1",
  roundNumber: 2,
  roundLabel: "First resubmittal",
  receivedAt: null,
  submittedByName: "Design firm",
  submittedByOrganization: null,
  status: "round_registered",
  summary: null,
  documentIds: ["doc_1"],
  carriedForwardItemIds: ["rmi_1"],
  documentCount: 1,
  carriedForwardItemCount: 1,
  createdByName: "Demo Reviewer",
  createdAt: null,
  updatedAt: null,
};

const summary = {
  resubmittalRoundId: "rr_1",
  projectId: "proj_1",
  roundNumber: 2,
  status: "documents_received",
  documentCount: 1,
  carriedForwardItemCount: 1,
  matrixItemCount: 1,
  applicantResponseSummary: { applicant_response_received: 1 },
  carryForwardSummary: { carried_forward_for_review: 1 },
};

const {
  createMatrixMock,
  recordResponseMock,
  updateItemMock,
  carryForwardMock,
  registerRoundMock,
  addFindingMock,
  linkDocumentMock,
} = vi.hoisted(() => ({
  createMatrixMock: vi.fn(),
  recordResponseMock: vi.fn(),
  updateItemMock: vi.fn(),
  carryForwardMock: vi.fn(),
  registerRoundMock: vi.fn(),
  addFindingMock: vi.fn(),
  linkDocumentMock: vi.fn(),
}));

beforeEach(() => {
  refreshMock.mockReset();
  createMatrixMock.mockReset();
  recordResponseMock.mockReset();
  updateItemMock.mockReset();
  carryForwardMock.mockReset();
  registerRoundMock.mockReset();
  addFindingMock.mockReset();
  linkDocumentMock.mockReset();
  createMatrixMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: matrix,
  });
  recordResponseMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: { ...item, applicantResponseStatus: "applicant_response_received" },
  });
  updateItemMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: item,
  });
  carryForwardMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: { ...item, carryForwardStatus: "carried_forward_for_review" },
  });
  registerRoundMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: round,
  });
  addFindingMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: item,
  });
  linkDocumentMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: round,
  });
});

afterEach(() => cleanup());

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDetail: vi.fn(async () => ok(project)),
    listResponseMatrices: vi.fn(async () => ok([matrix])),
    getResponseMatrix: vi.fn(async () => ok(matrix)),
    listResponseMatrixItems: vi.fn(async () => ok([item])),
    getResponseMatrixItem: vi.fn(async () => ok(item)),
    listResubmittalRounds: vi.fn(async () => ok([round])),
    getResubmittalRound: vi.fn(async () => ok(round)),
    getResubmittalRoundSummary: vi.fn(async () => ok(summary)),
    createResponseMatrix: createMatrixMock,
    recordApplicantResponse: recordResponseMock,
    updateResponseMatrixItem: updateItemMock,
    carryForwardMatrixItem: carryForwardMock,
    registerResubmittalRound: registerRoundMock,
    addFindingToMatrix: addFindingMock,
    linkDocumentToResubmittalRound: linkDocumentMock,
  };
});

import ResponseMatrixLandingPage from "@/app/projects/[projectId]/response-matrix/page";
import ResponseMatrixDetailPage from "@/app/projects/[projectId]/response-matrix/[matrixId]/page";
import ResponseMatrixItemDetailPage from "@/app/projects/[projectId]/response-matrix/items/[itemId]/page";
import ResubmittalRoundsPage from "@/app/projects/[projectId]/resubmittals/page";
import ResubmittalRoundDetailPage from "@/app/projects/[projectId]/resubmittals/[roundId]/page";
import ProjectDetailPage from "@/app/projects/[projectId]/page";
import CreateResponseMatrixButton from "@/components/CreateResponseMatrixButton";
import MatrixItemActions from "@/components/MatrixItemActions";
import RegisterResubmittalRound from "@/components/RegisterResubmittalRound";
import AddToResponseMatrixButton from "@/components/AddToResponseMatrixButton";
import LinkDocumentToResubmittalRound from "@/components/LinkDocumentToResubmittalRound";

const projectId = "proj_1";

describe("Response matrix landing page", () => {
  it("lists matrices and links to each one", async () => {
    const { container } = render(
      await ResponseMatrixLandingPage({ params: Promise.resolve({ projectId }) }),
    );
    expect(screen.getByText("Brookside response matrix")).toBeInTheDocument();
    const hrefs = Array.from(container.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    expect(hrefs).toContain(`/projects/${projectId}/response-matrix/rm_1`);
  });
});

describe("Create response matrix button", () => {
  it("calls createResponseMatrix and refreshes", async () => {
    render(<CreateResponseMatrixButton projectId={projectId} />);
    fireEvent.click(screen.getByText("Create response matrix"));
    await waitFor(() => expect(createMatrixMock).toHaveBeenCalled());
    expect(createMatrixMock.mock.calls[0][0]).toBe(projectId);
    await waitFor(() => expect(refreshMock).toHaveBeenCalled());
  });
});

describe("Response matrix detail page", () => {
  it("renders the item table with status labels", async () => {
    render(
      await ResponseMatrixDetailPage({
        params: Promise.resolve({ projectId, matrixId: "rm_1" }),
      }),
    );
    expect(screen.getByText("Detention and outlet control")).toBeInTheDocument();
    expect(screen.getAllByText("awaiting_applicant_response").length).toBeGreaterThan(
      0,
    );
  });
});

describe("Response matrix item detail page", () => {
  it("renders the reviewer comment draft and the action panel", async () => {
    render(
      await ResponseMatrixItemDetailPage({
        params: Promise.resolve({ projectId, itemId: "rmi_1" }),
      }),
    );
    expect(
      screen.getByText(/Provide a stage storage table/),
    ).toBeInTheDocument();
    expect(screen.getByText("Record applicant response")).toBeInTheDocument();
  });
});

describe("Matrix item actions", () => {
  it("records an applicant response with the typed text", async () => {
    render(<MatrixItemActions projectId={projectId} item={item} />);
    const textarea = screen.getByPlaceholderText("Recorded applicant response text");
    fireEvent.change(textarea, { target: { value: "We added the table." } });
    fireEvent.click(screen.getByText("Record response"));
    await waitFor(() => expect(recordResponseMock).toHaveBeenCalled());
    const call = recordResponseMock.mock.calls[0];
    expect(call[1]).toBe("rmi_1");
    expect(call[2].applicantResponseText).toBe("We added the table.");
  });

  it("carries the item forward with a safe carry-forward status", async () => {
    render(<MatrixItemActions projectId={projectId} item={item} />);
    fireEvent.click(screen.getByText("Carry forward for review"));
    await waitFor(() => expect(carryForwardMock).toHaveBeenCalled());
    const call = carryForwardMock.mock.calls[0];
    expect(call[2].carryForwardStatus).toBe("carried_forward_for_review");
  });
});

describe("Resubmittal rounds page", () => {
  it("lists rounds and links to each round", async () => {
    const { container } = render(
      await ResubmittalRoundsPage({ params: Promise.resolve({ projectId }) }),
    );
    expect(screen.getByText(/First resubmittal/)).toBeInTheDocument();
    const hrefs = Array.from(container.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    expect(hrefs).toContain(`/projects/${projectId}/resubmittals/rr_1`);
  });
});

describe("Register resubmittal round", () => {
  it("registers a round with the entered label", async () => {
    render(<RegisterResubmittalRound projectId={projectId} />);
    fireEvent.change(screen.getByPlaceholderText("First resubmittal"), {
      target: { value: "Second resubmittal" },
    });
    fireEvent.click(screen.getByText("Register resubmittal round"));
    await waitFor(() => expect(registerRoundMock).toHaveBeenCalled());
    const call = registerRoundMock.mock.calls[0];
    expect(call[1].roundLabel).toBe("Second resubmittal");
  });
});

describe("Resubmittal round detail page", () => {
  it("renders linked documents and the status summary", async () => {
    render(
      await ResubmittalRoundDetailPage({
        params: Promise.resolve({ projectId, roundId: "rr_1" }),
      }),
    );
    expect(screen.getByText("Linked documents")).toBeInTheDocument();
    expect(screen.getByText("1 matrix item(s) connected.")).toBeInTheDocument();
  });
});

describe("Add to response matrix button", () => {
  it("adds a finding to the selected matrix", async () => {
    render(
      <AddToResponseMatrixButton
        projectId={projectId}
        sourceType="finding"
        sourceId="find_1"
        matrices={[matrix]}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Add to response matrix" }),
    );
    await waitFor(() => expect(addFindingMock).toHaveBeenCalled());
    const call = addFindingMock.mock.calls[0];
    expect(call[1]).toBe("rm_1");
    expect(call[2]).toBe("find_1");
  });

  it("prompts to create a matrix when none exist", () => {
    render(
      <AddToResponseMatrixButton
        projectId={projectId}
        sourceType="finding"
        sourceId="find_1"
        matrices={[]}
      />,
    );
    expect(
      screen.getByText(/No response matrix exists for this project yet/),
    ).toBeInTheDocument();
  });
});

describe("Link document to resubmittal round", () => {
  it("links a document to the selected round", async () => {
    render(
      <LinkDocumentToResubmittalRound
        projectId={projectId}
        documentId="doc_1"
        rounds={[round]}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Link to resubmittal round" }),
    );
    await waitFor(() => expect(linkDocumentMock).toHaveBeenCalled());
    const call = linkDocumentMock.mock.calls[0];
    expect(call[1]).toBe("rr_1");
    expect(call[2]).toBe("doc_1");
  });
});

describe("Project overview Sprint 7 links", () => {
  it("links to the response matrix and resubmittal rounds", async () => {
    const { container } = render(
      await ProjectDetailPage({ params: Promise.resolve({ projectId }) }),
    );
    const hrefs = Array.from(container.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    expect(hrefs).toContain(`/projects/${projectId}/response-matrix`);
    expect(hrefs).toContain(`/projects/${projectId}/resubmittals`);
  });
});

describe("Professional boundary in Sprint 7 UI", () => {
  it("uses no prohibited final-decision wording and leaks no secrets", async () => {
    const parts: string[] = [];
    parts.push(
      (
        render(await ResponseMatrixLandingPage({ params: Promise.resolve({ projectId }) }))
          .container.textContent ?? ""
      ).toLowerCase(),
    );
    parts.push(
      (
        render(
          await ResponseMatrixItemDetailPage({
            params: Promise.resolve({ projectId, itemId: "rmi_1" }),
          }),
        ).container.textContent ?? ""
      ).toLowerCase(),
    );
    parts.push(
      (
        render(await ResubmittalRoundsPage({ params: Promise.resolve({ projectId }) })).container
          .textContent ?? ""
      ).toLowerCase(),
    );
    parts.push(
      (
        render(<MatrixItemActions projectId={projectId} item={item} />).container
          .textContent ?? ""
      ).toLowerCase(),
    );
    const text = parts.join(" ");
    for (const word of PROHIBITED_WORDS) {
      expect(text).not.toContain(word);
    }
    for (const leak of FORBIDDEN_LEAKS) {
      expect(text).not.toContain(leak);
    }
  });
});
