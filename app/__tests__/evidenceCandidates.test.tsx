import { ok } from "@/lib/api/__tests__/testHelpers";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  candidate,
  chunkSearchResponse,
  document,
  project,
  promoteResponse,
  searchResponse,
} from "./helpers/evidenceRetrievalFixtures";

const pushMock = vi.fn();
const refreshMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

afterEach(() => {
  cleanup();
  pushMock.mockReset();
  refreshMock.mockReset();
});

const {
  searchEvidenceMock,
  searchChunkEvidenceMock,
  saveCandidateMock,
  promoteMock,
  buildChunksMock,
} = vi.hoisted(() => ({
  searchEvidenceMock: vi.fn(),
  searchChunkEvidenceMock: vi.fn(),
  saveCandidateMock: vi.fn(),
  promoteMock: vi.fn(),
  buildChunksMock: vi.fn(),
}));

beforeEach(() => {
  searchEvidenceMock.mockReset();
  searchChunkEvidenceMock.mockReset();
  saveCandidateMock.mockReset();
  promoteMock.mockReset();
  buildChunksMock.mockReset();
  searchEvidenceMock.mockResolvedValue(searchResponse);
  searchChunkEvidenceMock.mockResolvedValue(chunkSearchResponse);
  saveCandidateMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: candidate,
  });
  promoteMock.mockResolvedValue(promoteResponse);
  buildChunksMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: {
      documentId: "doc_user_1",
      projectId: "proj_user_1",
      documentType: "stormwater_report",
      fileName: "Plan Set.pdf",
      pagesChunked: 2,
      chunkCount: 3,
      removedPriorChunkCount: 0,
    },
  });
});

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDetail: vi.fn(async () => ok(project)),
    listProjectDocuments: vi.fn(async () => ok([document])),
    listProjectEvidenceCandidates: vi.fn(async () => ok([candidate])),
    getEvidenceCandidate: vi.fn(async () => ok(candidate)),
    searchProjectEvidence: searchEvidenceMock,
    searchProjectChunkEvidence: searchChunkEvidenceMock,
    saveEvidenceCandidate: saveCandidateMock,
    promoteCandidateToDraftFinding: promoteMock,
    buildDocumentChunks: buildChunksMock,
    getProjectDocument: vi.fn(async () => ok(document)),
    listResubmittalRounds: vi.fn(async () => ok([])),
    getProjectFinding: vi.fn(async () => ok(null)),
    listFindingCitations: vi.fn(async () => ok([])),
  };
});

import EvidenceSearchClient from "@/components/EvidenceSearchClient";
import PromoteCandidateForm from "@/components/PromoteCandidateForm";
import EvidenceCandidateQueuePage from "@/app/projects/[projectId]/evidence-candidates/page";
import EvidenceCandidateDetailPage from "@/app/projects/[projectId]/evidence-candidates/[candidateId]/page";

const projectId = "proj_user_1";

describe("Evidence search client", () => {
  it("saves a candidate with citation fields and candidate origin", async () => {
    render(
      <EvidenceSearchClient
        projectId={projectId}
        documents={[]}
        documentTypes={[]}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("detention basin outlet"), {
      target: { value: "detention basin" },
    });
    fireEvent.click(screen.getByText("Search real-derived chunk evidence"));
    await waitFor(() => screen.getByText("Save candidate"));
    fireEvent.click(screen.getByText("Save candidate"));
    await waitFor(() => {
      expect(saveCandidateMock).toHaveBeenCalled();
    });
    const call = saveCandidateMock.mock.calls[0] as unknown as [
      string,
      {
        documentId: string;
        documentPageId: string | null;
        pageNumber: number | null;
        candidateOrigin: string;
        candidateStatus: string;
        candidateTitle: string;
        rankingScore: number;
      },
    ];
    expect(call[1].documentId).toBe("doc_user_1");
    expect(call[1].documentPageId).toBe("docpage_1");
    expect(call[1].pageNumber).toBe(2);
    expect(call[1].candidateOrigin).toBe("chunk_search");
    // The default "Save candidate" action persists the saved-for-review status.
    expect(call[1].candidateStatus).toBe("saved_for_review");
    expect(call[1].candidateTitle).toContain("Plan Set.pdf page 2");
    // After saving, a reviewer-controlled link to promote the candidate appears.
    await waitFor(() =>
      expect(screen.getByText("Review / promote candidate")).toBeInTheDocument(),
    );
    // The displayed status comes from the backend response, not the request.
    expect(screen.getByText(/Saved \(saved_for_review\)/)).toBeInTheDocument();
  });

  it("persists the triage status for the draft-queue action", async () => {
    saveCandidateMock.mockResolvedValueOnce({
      ok: true,
      backendReachable: true,
      data: { ...candidate, candidateStatus: "needs_reviewer_triage" },
    });
    render(
      <EvidenceSearchClient
        projectId={projectId}
        documents={[]}
        documentTypes={[]}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("detention basin outlet"), {
      target: { value: "detention basin" },
    });
    fireEvent.click(screen.getByText("Search real-derived chunk evidence"));
    await waitFor(() => screen.getByText("Add to draft queue"));
    fireEvent.click(screen.getByText("Add to draft queue"));
    await waitFor(() => expect(saveCandidateMock).toHaveBeenCalled());
    const call = saveCandidateMock.mock.calls[0] as unknown as [
      string,
      { candidateStatus: string },
    ];
    expect(call[1].candidateStatus).toBe("needs_reviewer_triage");
    await waitFor(() =>
      expect(
        screen.getByText(/Saved \(needs_reviewer_triage\)/),
      ).toBeInTheDocument(),
    );
  });

  it("displays only the status returned by the backend", async () => {
    // The reviewer clicks the triage action, but the backend returns a
    // saved_for_review status. The UI must show the backend value, not the
    // requested one (no optimistic status that was never persisted).
    saveCandidateMock.mockResolvedValueOnce({
      ok: true,
      backendReachable: true,
      data: { ...candidate, candidateStatus: "saved_for_review" },
    });
    render(
      <EvidenceSearchClient
        projectId={projectId}
        documents={[]}
        documentTypes={[]}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("detention basin outlet"), {
      target: { value: "detention basin" },
    });
    fireEvent.click(screen.getByText("Search real-derived chunk evidence"));
    await waitFor(() => screen.getByText("Add to draft queue"));
    fireEvent.click(screen.getByText("Add to draft queue"));
    await waitFor(() =>
      expect(screen.getByText(/Saved \(saved_for_review\)/)).toBeInTheDocument(),
    );
    expect(
      screen.queryByText(/Saved \(needs_reviewer_triage\)/),
    ).not.toBeInTheDocument();
  });
});

describe("Evidence candidate queue page", () => {
  it("renders saved candidates", async () => {
    render(await EvidenceCandidateQueuePage({ params: Promise.resolve({ projectId }) }));
    expect(screen.getByText("Evidence candidate queue")).toBeInTheDocument();
    expect(screen.getByText("Plan Set.pdf page 2")).toBeInTheDocument();
    expect(screen.getByText("saved_for_review")).toBeInTheDocument();
  });
});

describe("Evidence candidate detail page", () => {
  it("renders the candidate and the promote form", async () => {
    render(
      await EvidenceCandidateDetailPage({
        params: Promise.resolve({ projectId, candidateId: "cand_1" }),
      }),
    );
    expect(
      screen.getByText("Promote to reviewer draft finding"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/This creates a reviewer draft finding/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Dismiss candidate")).toBeInTheDocument();
  });
});

describe("Promote candidate form", () => {
  it("submits a safe reviewer draft status payload", async () => {
    render(
      <PromoteCandidateForm
        projectId={projectId}
        candidateId="cand_1"
        defaultTitle="Plan Set.pdf page 2"
        defaultExcerpt="...detention basin outlet..."
        alreadyPromoted={false}
        promotedFindingId={null}
      />,
    );
    fireEvent.click(screen.getByText("Create reviewer draft finding"));
    await waitFor(() => {
      expect(promoteMock).toHaveBeenCalled();
    });
    const call = promoteMock.mock.calls[0] as unknown as [
      string,
      string,
      { riskLevel: string },
    ];
    expect(call[0]).toBe(projectId);
    expect(call[1]).toBe("cand_1");
    // Risk level is reviewer-entered, defaulting to a non-final value.
    expect(call[2].riskLevel).toBe("medium");
  });
});
