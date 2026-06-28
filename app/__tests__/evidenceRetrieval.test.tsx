import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();
const refreshMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "fully compliant",
  "passes review",
  "validated",
  "resolved",
  "closed",
];

afterEach(() => {
  cleanup();
  pushMock.mockReset();
  refreshMock.mockReset();
});

const project = {
  projectId: "proj_user_1",
  projectName: "Retrieval Project",
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
  sourceMode: "user_created",
  createdByName: "Demo Reviewer",
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
  findingCount: 0,
  auditEventCount: 1,
};

const document = {
  documentId: "doc_user_1",
  projectId: "proj_user_1",
  fileName: "doc_abc.pdf",
  originalFileName: "Plan Set.pdf",
  documentType: "stormwater_report",
  status: "uploaded",
  purpose: "",
  expectedKeyInformation: "",
  sourceMode: "user_uploaded",
  uploadStatus: "stored",
  processingStatus: "indexed_with_text",
  contentType: "application/pdf",
  fileSizeBytes: 1,
  checksumSha256: "abc",
  revisionLabel: null,
  revisionDate: null,
  uploadedByName: "Demo Reviewer",
  uploadedAt: null,
  registeredAt: null,
  pageCount: 2,
  indexedAt: null,
  textExtractionStatus: "text_extracted",
  textExtractionSummary: null,
  extractionWarningCount: 0,
};

const candidate = {
  evidenceCandidateId: "cand_1",
  projectId: "proj_user_1",
  retrievalQueryId: "rq_user_1",
  documentId: "doc_user_1",
  documentPageId: "docpage_1",
  pageNumber: 2,
  findingId: null,
  checklistItemId: null,
  candidateTitle: "Plan Set.pdf page 2",
  candidateExcerpt: "...detention basin outlet...",
  matchTerms: ["detention", "basin"],
  rankingScore: 0.82,
  rankingReason: "Ranked by keyword match.",
  candidateStatus: "saved_for_review",
  candidateOrigin: "keyword_search",
  reviewerNote: null,
  createdByName: "Demo Reviewer",
  createdAt: null,
  updatedAt: null,
  dismissedAt: null,
  promotedFindingId: null,
};

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

const searchResponse = {
  ok: true,
  backendReachable: true,
  data: {
    projectId: "proj_user_1",
    queryText: "detention basin",
    queryType: "keyword",
    retrievalQueryId: "rq_user_1",
    resultCount: 1,
    results: [
      {
        documentId: "doc_user_1",
        documentName: "Plan Set.pdf",
        documentType: "stormwater_report",
        documentPageId: "docpage_1",
        pageNumber: 2,
        pageLabel: "Page 2",
        textExtractionStatus: "text_extracted",
        excerpt: "...detention basin outlet...",
        matchTerms: ["detention", "basin"],
        rankingScore: 0.82,
        rankingReason: "Ranked by keyword match: detention, basin.",
        candidateOrigin: "keyword_search",
        retrievalQueryId: "rq_user_1",
      },
    ],
    message: "1 retrieval candidate(s) for reviewer review.",
  },
};

const chunkSearchResponse = {
  ok: true,
  backendReachable: true,
  data: {
    projectId: "proj_user_1",
    queryText: "detention basin",
    queryType: "chunk_keyword",
    retrievalQueryId: "rq_user_2",
    resultCount: 1,
    results: [
      {
        documentId: "doc_user_1",
        documentName: "Plan Set.pdf",
        documentType: "stormwater_report",
        chunkId: "rdc_doc_user_1_p2_0",
        documentPageId: "docpage_1",
        pageNumber: 2,
        pageLabel: "Page 2",
        textExtractionStatus: "text_extracted",
        excerpt: "...detention basin outlet...",
        matchTerms: ["detention", "basin"],
        rankingScore: 0.78,
        rankingReason:
          "Ranked by keyword match: detention, basin in real-derived page chunk.",
        candidateOrigin: "chunk_search",
        retrievalQueryId: "rq_user_2",
      },
    ],
    message: "1 real-derived chunk candidate(s) for reviewer review.",
  },
};

const chunkEmptyResponse = {
  ok: true,
  backendReachable: true,
  data: {
    projectId: "proj_user_1",
    queryText: "nomatch",
    queryType: "chunk_keyword",
    retrievalQueryId: "rq_user_3",
    resultCount: 0,
    results: [],
    message:
      "No real-derived chunk text matched these terms. Try different terms or " +
      "filters. This is not a finding about the document content.",
  },
};

const promoteResponse = {
  ok: true,
  backendReachable: true,
  data: {
    finding: {
      findingId: "find_draft_1",
      projectId: "proj_user_1",
      title: "Outlet sizing draft",
      category: "stormwater",
      riskLevel: "medium",
      evidenceStatus: "needs_reviewer_confirmation",
      humanReviewStatus: "draft",
      findingOrigin: "retrieval_candidate",
      sourceMode: "user_created",
      createdByName: "Demo Reviewer",
    },
    citation: {
      evidenceCitationId: "cite_1",
      projectId: "proj_user_1",
      findingId: "find_draft_1",
      documentId: "doc_user_1",
      documentPageId: "docpage_1",
      pageNumber: 2,
      citationType: "reviewer_selected",
      citationStatus: "needs_reviewer_confirmation",
    },
    candidate: { ...candidate, candidateStatus: "promoted_to_draft" },
  },
};

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
    getProjectDetail: vi.fn(async () => project),
    listProjectDocuments: vi.fn(async () => [document]),
    listProjectEvidenceCandidates: vi.fn(async () => [candidate]),
    getEvidenceCandidate: vi.fn(async () => candidate),
    searchProjectEvidence: searchEvidenceMock,
    searchProjectChunkEvidence: searchChunkEvidenceMock,
    saveEvidenceCandidate: saveCandidateMock,
    promoteCandidateToDraftFinding: promoteMock,
    buildDocumentChunks: buildChunksMock,
    getProjectDocument: vi.fn(async () => document),
    listResubmittalRounds: vi.fn(async () => []),
    getProjectFinding: vi.fn(async () => null),
    listFindingCitations: vi.fn(async () => []),
  };
});

import EvidenceSearchClient from "@/components/EvidenceSearchClient";
import BuildChunksButton from "@/components/BuildChunksButton";
import PromoteCandidateForm from "@/components/PromoteCandidateForm";
import EvidenceSearchPage from "@/app/projects/[projectId]/evidence-search/page";
import EvidenceCandidateQueuePage from "@/app/projects/[projectId]/evidence-candidates/page";
import EvidenceCandidateDetailPage from "@/app/projects/[projectId]/evidence-candidates/[candidateId]/page";
import ProjectDetailPage from "@/app/projects/[projectId]/page";

const projectId = "proj_user_1";

describe("Evidence search page", () => {
  it("renders the search form and candidate-confirmation copy", async () => {
    render(await EvidenceSearchPage({ params: { projectId } }));
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

describe("Evidence candidate queue page", () => {
  it("renders saved candidates", async () => {
    render(await EvidenceCandidateQueuePage({ params: { projectId } }));
    expect(screen.getByText("Evidence candidate queue")).toBeInTheDocument();
    expect(screen.getByText("Plan Set.pdf page 2")).toBeInTheDocument();
    expect(screen.getByText("saved_for_review")).toBeInTheDocument();
  });
});

describe("Evidence candidate detail page", () => {
  it("renders the candidate and the promote form", async () => {
    render(
      await EvidenceCandidateDetailPage({
        params: { projectId, candidateId: "cand_1" },
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

describe("Project overview links", () => {
  it("links to evidence search and the candidate queue", async () => {
    const { container } = render(
      await ProjectDetailPage({ params: { projectId } }),
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
        params: { projectId, candidateId: "cand_1" },
      }),
    );
    const { container: c2 } = render(
      await EvidenceCandidateQueuePage({ params: { projectId } }),
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
