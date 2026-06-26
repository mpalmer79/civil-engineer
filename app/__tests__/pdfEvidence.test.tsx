import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

// Mock next/navigation for client components and server-page notFound.
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
  "verified citation",
  "approved citation",
];

afterEach(() => {
  cleanup();
  pushMock.mockReset();
  refreshMock.mockReset();
  vi.restoreAllMocks();
});

const userDoc = {
  documentId: "doc_user_1",
  projectId: "proj_user_1",
  fileName: "doc_abc.pdf",
  originalFileName: "Stormwater Report.pdf",
  documentType: "stormwater_report",
  status: "uploaded",
  purpose: "narrative",
  expectedKeyInformation: "",
  sourceMode: "user_uploaded",
  uploadStatus: "stored",
  processingStatus: "indexed_with_text",
  contentType: "application/pdf",
  fileSizeBytes: 1234,
  checksumSha256: "abc",
  revisionLabel: null,
  revisionDate: null,
  uploadedByName: "Demo Reviewer",
  uploadedAt: "2026-06-26T00:00:00Z",
  registeredAt: "2026-06-26T00:00:00Z",
  pageCount: 2,
  indexedAt: "2026-06-26T00:00:00Z",
  textExtractionStatus: "text_extracted",
  textExtractionSummary: "2 page(s) indexed: 2 with extractable text.",
  extractionWarningCount: 0,
};

const csvDoc = {
  ...userDoc,
  documentId: "doc_user_2",
  fileName: "doc_def.csv",
  originalFileName: "data.csv",
  contentType: "text/csv",
  processingStatus: "uploaded",
  pageCount: null,
  indexedAt: null,
  textExtractionStatus: null,
  textExtractionSummary: null,
};

const page = {
  documentPageId: "docpage_1",
  projectId: "proj_user_1",
  documentId: "doc_user_1",
  pageNumber: 1,
  pageLabel: "Page 1",
  extractedText: "Outlet detail on page one",
  textExtractionStatus: "text_extracted",
  textExtractionMethod: "pypdf_text_layer",
  charCount: 25,
  wordCount: 5,
  extractionWarnings: [],
  indexedAt: "2026-06-26T00:00:00Z",
};

const noTextPage = {
  ...page,
  documentPageId: "docpage_2",
  extractedText: null,
  textExtractionStatus: "no_extractable_text",
  charCount: 0,
  wordCount: 0,
};

const finding = {
  findingId: "find_user_1",
  projectId: "proj_user_1",
  title: "Detention basin outlet detail missing",
  category: "stormwater",
  riskLevel: "high",
  evidenceStatus: "missing_evidence",
  evidenceToFind: "Outlet detail",
  reasonItMatters: "Controls release rate",
  recommendedHumanAction: "Request the outlet detail",
  humanReviewStatus: "needs_reviewer_confirmation",
  relatedDocuments: [],
  sourceMode: "user_created",
  findingOrigin: "reviewer_created",
  reviewerNotes: null,
  createdByName: "Demo Reviewer",
  createdAt: null,
};

const citation = {
  evidenceCitationId: "cite_1",
  projectId: "proj_user_1",
  findingId: "find_user_1",
  documentId: "doc_user_1",
  documentPageId: "docpage_1",
  pageNumber: 1,
  pageLabel: "Page 1",
  sectionLabel: "Outlet detail",
  quotedExcerpt: "Outlet detail on page one",
  reviewerNote: "Supports the finding",
  citationType: "reviewer_selected",
  citationStatus: "needs_reviewer_confirmation",
  createdByName: "Demo Reviewer",
  sourceMode: "user_created",
  createdAt: null,
  updatedAt: null,
};

const project = {
  projectId: "proj_user_1",
  projectName: "PDF Project",
  projectType: "Commercial",
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
  findingCount: 1,
  auditEventCount: 3,
};

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDocument: vi.fn(async (_p: string, id: string) =>
      id === "doc_user_2" ? csvDoc : userDoc,
    ),
    listProjectDocuments: vi.fn(async () => [userDoc, csvDoc]),
    listDocumentPages: vi.fn(async () => [page, noTextPage]),
    getDocumentPage: vi.fn(async (_p: string, _d: string, n: number) =>
      n === 2 ? noTextPage : page,
    ),
    getProjectDetail: vi.fn(async () => project),
    getProjectFinding: vi.fn(async () => finding),
    listProjectFindings: vi.fn(async () => [finding]),
    listFindingCitations: vi.fn(async () => [citation]),
    listProjectEvidenceCitations: vi.fn(async () => [citation]),
    indexPdfDocument: vi.fn(async () => ({
      ok: true,
      backendReachable: true,
      data: {
        documentId: "doc_user_1",
        pageCount: 2,
        pagesWithText: 2,
        pagesWithoutText: 0,
        warningCount: 0,
        processingStatus: "indexed_with_text",
        textExtractionStatus: "text_extracted",
        indexedAt: "2026-06-26T00:00:00Z",
        summary: "2 page(s) indexed: 2 with extractable text.",
      },
    })),
    createEvidenceCitation: vi.fn(async () => ({
      ok: true,
      backendReachable: true,
      data: citation,
    })),
  };
});

import * as api from "@/lib/api";
import DocumentDetailPage from "@/app/projects/[projectId]/documents/[documentId]/page";
import DocumentPagesPage from "@/app/projects/[projectId]/documents/[documentId]/pages/page";
import DocumentPageDetail from "@/app/projects/[projectId]/documents/[documentId]/pages/[pageNumber]/page";
import FindingDetailPage from "@/app/projects/[projectId]/findings/[findingId]/page";
import ProjectEvidenceCitationsPage from "@/app/projects/[projectId]/evidence-citations/page";
import ProjectDocumentsPage from "@/app/projects/[projectId]/documents/page";
import EvidenceCitationForm from "@/components/EvidenceCitationForm";

const projectId = "proj_user_1";

describe("Project documents list", () => {
  it("shows processing status and page count", async () => {
    render(await ProjectDocumentsPage({ params: { projectId } }));
    expect(screen.getByText("indexed_with_text")).toBeInTheDocument();
    expect(screen.getByText("Text extraction")).toBeInTheDocument();
    expect(screen.getByText("text_extracted")).toBeInTheDocument();
  });
});

describe("Document detail page", () => {
  it("renders the index action for a PDF with a stored file", async () => {
    render(
      await DocumentDetailPage({
        params: { projectId, documentId: "doc_user_1" },
      }),
    );
    expect(screen.getByText("Index PDF pages")).toBeInTheDocument();
    expect(screen.getByText("View pages")).toBeInTheDocument();
  });

  it("disables indexing for a non-PDF document", async () => {
    render(
      await DocumentDetailPage({
        params: { projectId, documentId: "doc_user_2" },
      }),
    );
    expect(screen.getByText(/not a PDF/i)).toBeInTheDocument();
    expect(screen.queryByText("Index PDF pages")).not.toBeInTheDocument();
  });
});

describe("Document pages index", () => {
  it("renders page rows", async () => {
    render(
      await DocumentPagesPage({
        params: { projectId, documentId: "doc_user_1" },
      }),
    );
    expect(screen.getAllByText("text_extracted").length).toBeGreaterThan(0);
    expect(screen.getByText("no_extractable_text")).toBeInTheDocument();
    expect(screen.getAllByText("View page").length).toBe(2);
  });
});

describe("Document page detail", () => {
  it("renders extracted text preview", async () => {
    render(
      await DocumentPageDetail({
        params: { projectId, documentId: "doc_user_1", pageNumber: "1" },
      }),
    );
    expect(screen.getByText("Outlet detail on page one")).toBeInTheDocument();
    expect(screen.getByText("Cite this page as evidence")).toBeInTheDocument();
  });

  it("renders a no-text message for a scanned page", async () => {
    render(
      await DocumentPageDetail({
        params: { projectId, documentId: "doc_user_1", pageNumber: "2" },
      }),
    );
    expect(screen.getByText(/No extractable text on this page/i)).toBeInTheDocument();
  });
});

describe("Evidence citation form", () => {
  it("renders and submits the expected payload", async () => {
    render(
      <EvidenceCitationForm
        projectId={projectId}
        documentId="doc_user_1"
        pageNumber={1}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("find_user_..."), {
      target: { value: "find_user_1" },
    });
    fireEvent.click(screen.getByText("Create evidence citation"));
    await waitFor(() => {
      expect(api.createEvidenceCitation).toHaveBeenCalled();
    });
    const call = (api.createEvidenceCitation as unknown as ReturnType<typeof vi.fn>)
      .mock.calls[0];
    expect(call[0]).toBe(projectId);
    expect(call[1]).toBe("find_user_1");
    expect(call[2]).toMatchObject({ documentId: "doc_user_1", pageNumber: 1 });
  });
});

describe("Finding detail page", () => {
  it("shows the evidence citation section", async () => {
    render(
      await FindingDetailPage({
        params: { projectId, findingId: "find_user_1" },
      }),
    );
    expect(screen.getByText("Evidence citations")).toBeInTheDocument();
    expect(screen.getAllByText(/Outlet detail/).length).toBeGreaterThan(0);
  });
});

describe("Project evidence citations page", () => {
  it("renders the citations table", async () => {
    render(await ProjectEvidenceCitationsPage({ params: { projectId } }));
    expect(
      screen.getByText("Detention basin outlet detail missing"),
    ).toBeInTheDocument();
    expect(screen.getByText("Stormwater Report.pdf")).toBeInTheDocument();
  });
});

describe("Professional boundary in new Sprint 2 UI", () => {
  it("uses no prohibited final-decision wording", async () => {
    const { container: c1 } = render(
      await DocumentPageDetail({
        params: { projectId, documentId: "doc_user_1", pageNumber: "1" },
      }),
    );
    const { container: c2 } = render(
      await FindingDetailPage({
        params: { projectId, findingId: "find_user_1" },
      }),
    );
    const { container: c3 } = render(
      <EvidenceCitationForm projectId={projectId} documentId="doc_user_1" pageNumber={1} />,
    );
    const text = (
      (c1.textContent ?? "") +
      (c2.textContent ?? "") +
      (c3.textContent ?? "")
    ).toLowerCase();
    for (const word of PROHIBITED_WORDS) {
      expect(text).not.toContain(word);
    }
  });
});
