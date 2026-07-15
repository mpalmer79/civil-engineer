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
  chunkEmptyResponse,
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
import EvidenceSearchPage from "@/app/projects/[projectId]/evidence-search/page";

const projectId = "proj_user_1";

describe("Evidence search page", () => {
  it("renders the search form and candidate-confirmation copy", async () => {
    render(await EvidenceSearchPage({ params: Promise.resolve({ projectId }) }));
    expect(screen.getByText("Evidence search")).toBeInTheDocument();
    expect(
      screen.getByText(/Evidence candidates require reviewer confirmation/i),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("detention basin outlet"),
    ).toBeInTheDocument();
  });
});

describe("Evidence search client", () => {
  it("defaults to real-derived chunk search and renders citation context", async () => {
    render(
      <EvidenceSearchClient
        projectId={projectId}
        documents={[
          {
            documentId: "doc_user_1",
            label: "Plan Set.pdf",
            documentType: "stormwater_report",
          },
        ]}
        documentTypes={["stormwater_report"]}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("detention basin outlet"), {
      target: { value: "detention basin" },
    });
    fireEvent.click(screen.getByText("Search real-derived chunk evidence"));
    await waitFor(() => {
      expect(searchChunkEvidenceMock).toHaveBeenCalled();
    });
    expect(searchEvidenceMock).not.toHaveBeenCalled();
    const call = searchChunkEvidenceMock.mock.calls[0] as unknown as [
      string,
      { queryText: string },
    ];
    expect(call[0]).toBe(projectId);
    expect(call[1].queryText).toBe("detention basin");
    await waitFor(() => {
      expect(screen.getByText(/Plan Set.pdf, page 2/)).toBeInTheDocument();
    });
    // Page-level citation context is shown to support citation integrity.
    expect(screen.getByText(/relevance 0.78/)).toBeInTheDocument();
    expect(screen.getByText(/Text status: text_extracted/)).toBeInTheDocument();
    expect(screen.getByText(/Origin: chunk_search/)).toBeInTheDocument();
    expect(screen.getByText(/chunk id: rdc_/)).toBeInTheDocument();
  });

  it("defaults the chunk retrieval mode to hybrid and can switch modes", async () => {
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
    await waitFor(() => expect(searchChunkEvidenceMock).toHaveBeenCalled());
    let call = searchChunkEvidenceMock.mock.calls[0] as unknown as [
      string,
      { mode: string },
    ];
    expect(call[1].mode).toBe("hybrid");

    // Switch the retrieval mode to semantic and search again.
    fireEvent.change(screen.getByDisplayValue("Hybrid (keyword + semantic)"), {
      target: { value: "semantic" },
    });
    fireEvent.click(screen.getByText("Search real-derived chunk evidence"));
    await waitFor(() =>
      expect(searchChunkEvidenceMock).toHaveBeenCalledTimes(2),
    );
    call = searchChunkEvidenceMock.mock.calls[1] as unknown as [
      string,
      { mode: string },
    ];
    expect(call[1].mode).toBe("semantic");
  });

  it("renders a semantic note for results without match terms", async () => {
    searchChunkEvidenceMock.mockResolvedValueOnce({
      ok: true,
      backendReachable: true,
      data: {
        ...chunkSearchResponse.data,
        results: [
          {
            ...chunkSearchResponse.data.results[0],
            matchTerms: [],
            rankingReason:
              "Ranked by semantic similarity using chunk embedding.",
          },
        ],
      },
    });
    render(
      <EvidenceSearchClient
        projectId={projectId}
        documents={[]}
        documentTypes={[]}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("detention basin outlet"), {
      target: { value: "retention pond" },
    });
    fireEvent.click(screen.getByText("Search real-derived chunk evidence"));
    await waitFor(() =>
      expect(
        screen.getByText(/Semantic relevance \(no exact keyword terms\)/),
      ).toBeInTheDocument(),
    );
  });

  it("can switch to indexed page text search", async () => {
    render(
      <EvidenceSearchClient
        projectId={projectId}
        documents={[]}
        documentTypes={[]}
      />,
    );
    fireEvent.change(
      screen.getByDisplayValue("Real-derived chunk evidence"),
      { target: { value: "page_text" } },
    );
    fireEvent.change(screen.getByPlaceholderText("detention basin outlet"), {
      target: { value: "detention basin" },
    });
    fireEvent.click(screen.getByText("Search indexed page text"));
    await waitFor(() => {
      expect(searchEvidenceMock).toHaveBeenCalled();
    });
    expect(searchChunkEvidenceMock).not.toHaveBeenCalled();
  });

  it("shows an honest empty-state message that does not imply absence", async () => {
    searchChunkEvidenceMock.mockResolvedValueOnce(chunkEmptyResponse);
    render(
      <EvidenceSearchClient
        projectId={projectId}
        documents={[]}
        documentTypes={[]}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("detention basin outlet"), {
      target: { value: "nomatch" },
    });
    fireEvent.click(screen.getByText("Search real-derived chunk evidence"));
    await waitFor(() => {
      expect(
        screen.getByText(/not a finding about the document content/i),
      ).toBeInTheDocument();
    });
    expect(screen.queryByText("Save candidate")).not.toBeInTheDocument();
  });
});
