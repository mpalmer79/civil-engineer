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
  PROHIBITED_WORDS,
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
import BuildChunksButton from "@/components/BuildChunksButton";
import EvidenceCandidateQueuePage from "@/app/projects/[projectId]/evidence-candidates/page";
import EvidenceCandidateDetailPage from "@/app/projects/[projectId]/evidence-candidates/[candidateId]/page";
import ProjectDetailPage from "@/app/projects/[projectId]/page";

const projectId = "proj_user_1";

describe("Build page chunks button", () => {
  it("calls the chunk-pages endpoint and reports the result", async () => {
    render(
      <BuildChunksButton projectId={projectId} documentId="doc_user_1" />,
    );
    fireEvent.click(screen.getByText("Build page chunks"));
    await waitFor(() => {
      expect(buildChunksMock).toHaveBeenCalledWith(projectId, "doc_user_1");
    });
    await waitFor(() =>
      expect(
        screen.getByText(/3 real-derived chunk\(s\) built/),
      ).toBeInTheDocument(),
    );
  });

  it("is disabled with a reason when the document is not indexable", () => {
    render(
      <BuildChunksButton
        projectId={projectId}
        documentId="doc_user_1"
        disabled
        disabledReason="Building page chunks requires an indexed PDF document."
      />,
    );
    expect(
      screen.getByText(/requires an indexed PDF document/),
    ).toBeInTheDocument();
    expect(screen.queryByText("Build page chunks")).not.toBeInTheDocument();
  });
});

describe("Project overview links", () => {
  it("links to evidence search and the candidate queue", async () => {
    const { container } = render(
      await ProjectDetailPage({ params: Promise.resolve({ projectId }) }),
    );
    const hrefs = Array.from(container.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    expect(hrefs).toContain(`/projects/${projectId}/evidence-search`);
    expect(hrefs).toContain(`/projects/${projectId}/evidence-candidates`);
  });
});

describe("Professional boundary in new Sprint 3 UI", () => {
  it("uses no prohibited final-decision wording", async () => {
    const { container: c1 } = render(
      await EvidenceCandidateDetailPage({
        params: Promise.resolve({ projectId, candidateId: "cand_1" }),
      }),
    );
    const { container: c2 } = render(
      await EvidenceCandidateQueuePage({ params: Promise.resolve({ projectId }) }),
    );
    const text = (
      (c1.textContent ?? "") + (c2.textContent ?? "")
    ).toLowerCase();
    for (const word of PROHIBITED_WORDS) {
      expect(text).not.toContain(word);
    }
  });
});

describe("Professional boundary in chunk evidence UI", () => {
  // The critical language boundary for the chunk evidence workflow.
  const BANNED = [
    "approve",
    "approved",
    "certify",
    "certified",
    "validate",
    "validated",
    "verify",
    "verified",
    "compliant",
    "compliance",
    "safe",
    "safety",
  ];

  it("introduces no banned vocabulary in the search UI", async () => {
    const { container } = render(
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
    const text = (container.textContent ?? "").toLowerCase();
    for (const word of BANNED) {
      expect(text).not.toContain(word);
    }
  });
});
