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

const { searchEvidenceMock, saveCandidateMock, promoteMock } = vi.hoisted(
  () => ({
    searchEvidenceMock: vi.fn(),
    saveCandidateMock: vi.fn(),
    promoteMock: vi.fn(),
  }),
);

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
  saveCandidateMock.mockReset();
  promoteMock.mockReset();
  searchEvidenceMock.mockResolvedValue(searchResponse);
  saveCandidateMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: candidate,
  });
  promoteMock.mockResolvedValue(promoteResponse);
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
    saveEvidenceCandidate: saveCandidateMock,
    promoteCandidateToDraftFinding: promoteMock,
    getProjectFinding: vi.fn(async () => null),
    listFindingCitations: vi.fn(async () => []),
  };
});

import EvidenceSearchClient from "@/components/EvidenceSearchClient";
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
  it("submits the expected payload and renders results", async () => {
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
    fireEvent.click(screen.getByText("Search indexed evidence"));
    await waitFor(() => {
      expect(searchEvidenceMock).toHaveBeenCalled();
    });
    const call = searchEvidenceMock.mock.calls[0] as unknown as [
      string,
      { queryText: string },
    ];
    expect(call[0]).toBe(projectId);
    expect(call[1].queryText).toBe("detention basin");
    await waitFor(() => {
      expect(screen.getByText(/Plan Set.pdf, page 2/)).toBeInTheDocument();
    });
    expect(screen.getByText(/relevance 0.82/)).toBeInTheDocument();
  });

  it("saves a candidate from a result", async () => {
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
    fireEvent.click(screen.getByText("Search indexed evidence"));
    await waitFor(() => screen.getByText("Save candidate"));
    fireEvent.click(screen.getByText("Save candidate"));
    await waitFor(() => {
      expect(saveCandidateMock).toHaveBeenCalled();
    });
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
