import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "compliant",
  "verified",
  "passed review",
  "resolved",
  "closed",
];

const { downloadMock } = vi.hoisted(() => ({ downloadMock: vi.fn() }));

beforeEach(() => {
  downloadMock.mockReset();
  downloadMock.mockResolvedValue({ ok: true, backendReachable: true });
});

afterEach(() => cleanup());

const baseDoc = {
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
  processingStatus: "parsing_not_available",
  contentType: "application/pdf",
  fileSizeBytes: 2048,
  checksumSha256: "abcdef0123456789abcdef",
  revisionLabel: null,
  revisionDate: null,
  uploadedByName: "Demo Reviewer",
  uploadedAt: null,
  registeredAt: null,
  pageCount: null,
  indexedAt: null,
  textExtractionStatus: null,
  textExtractionSummary: null,
  extractionWarningCount: 0,
  storageProvider: "local",
  fileAvailable: true,
  downloadCount: 3,
  lastDownloadedAt: null,
};

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDocument: vi.fn(async () => baseDoc),
    getProjectDetail: vi.fn(async () => ({
      projectId: "proj_user_1",
      projectName: "Storage Project",
    })),
    listProjectDocuments: vi.fn(async () => [
      baseDoc,
      { ...baseDoc, documentId: "doc_user_2", fileAvailable: false },
    ]),
    downloadDocument: downloadMock,
  };
});

import DocumentDetailPage from "@/app/projects/[projectId]/documents/[documentId]/page";
import ProjectDocumentsPage from "@/app/projects/[projectId]/documents/page";
import DocumentDownloadButton from "@/components/DocumentDownloadButton";

const projectId = "proj_user_1";

describe("Documents list page", () => {
  it("shows storage provider and file availability", async () => {
    render(await ProjectDocumentsPage({ params: { projectId } }));
    // Each document renders as a responsive card with labeled status chips.
    expect(screen.getAllByText("Storage").length).toBeGreaterThan(0);
    expect(screen.getAllByText("local").length).toBeGreaterThan(0);
    expect(screen.getByText("file available")).toBeInTheDocument();
    expect(screen.getByText("file unavailable")).toBeInTheDocument();
  });
});

describe("Document detail page", () => {
  it("shows the storage metadata card and a download button", async () => {
    render(
      await DocumentDetailPage({
        params: { projectId, documentId: "doc_user_1" },
      }),
    );
    expect(screen.getByText("Storage provider")).toBeInTheDocument();
    expect(screen.getByText("Download file")).toBeInTheDocument();
    // The raw storage path is never shown.
    expect(screen.queryByText(/project_uploads/)).not.toBeInTheDocument();
  });

  it("gates indexing on file availability", async () => {
    const apiModule = await import("@/lib/api");
    (apiModule.getProjectDocument as unknown as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ...baseDoc, fileAvailable: false });
    render(
      await DocumentDetailPage({
        params: { projectId, documentId: "doc_user_1" },
      }),
    );
    expect(
      screen.getAllByText(/not available in storage/i).length,
    ).toBeGreaterThan(0);
    expect(screen.queryByText("Index PDF pages")).not.toBeInTheDocument();
  });
});

describe("DocumentDownloadButton", () => {
  it("triggers a download when the file is available", async () => {
    render(
      <DocumentDownloadButton
        projectId={projectId}
        documentId="doc_user_1"
        fileName="Plan Set.pdf"
        available={true}
      />,
    );
    fireEvent.click(screen.getByText("Download file"));
    await waitFor(() => expect(downloadMock).toHaveBeenCalled());
    const call = downloadMock.mock.calls[0];
    expect(call[0]).toBe(projectId);
    expect(call[1]).toBe("doc_user_1");
  });

  it("shows a storage-unavailable message when the file is missing", () => {
    render(
      <DocumentDownloadButton
        projectId={projectId}
        documentId="doc_user_1"
        fileName="Plan Set.pdf"
        available={false}
      />,
    );
    expect(
      screen.getByText(/not available in storage/i),
    ).toBeInTheDocument();
    expect(screen.queryByText("Download file")).not.toBeInTheDocument();
  });
});

describe("Professional boundary in new Sprint 6 UI", () => {
  it("uses no prohibited final-decision wording", async () => {
    const { container } = render(
      await DocumentDetailPage({
        params: { projectId, documentId: "doc_user_1" },
      }),
    );
    const text = (container.textContent ?? "").toLowerCase();
    for (const word of PROHIBITED_WORDS) {
      expect(text).not.toContain(word);
    }
  });
});
