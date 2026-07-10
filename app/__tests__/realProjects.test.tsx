import fs from "node:fs";
import path from "node:path";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

// Mock next/navigation so client form components (useRouter) and server pages
// (notFound) render in jsdom without a Next.js runtime.
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

// Final-decision wording the new visible UI must never use as a status or
// conclusion. Mirrors the backend safety vocabulary.
const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "fully compliant",
  "engineer-confirmed",
  "passes review",
  "meets all requirements",
];

afterEach(() => {
  cleanup();
  pushMock.mockReset();
});

const demoProject = {
  projectId: "proj_brookside_meadows",
  projectName: "Brookside Meadows Residential Subdivision",
  projectType: "Residential subdivision",
  locationContext: "Suburban fringe",
  jurisdiction: "Town of Hartwell",
  reviewType: "Subdivision stormwater review",
  reviewDomain: "stormwater",
  acreage: 38.5,
  disturbedArea: 22,
  proposedLots: 47,
  status: "ready_for_review",
  summary: "Seeded demo fixture.",
  sourceMode: "demo_fixture",
  createdByName: null,
  applicantName: null,
  applicantOrganization: null,
  designEngineerName: null,
  designFirm: null,
  submissionReference: null,
  reviewRoundCurrent: 1,
  parcelIds: [],
  createdAt: null,
  updatedAt: null,
  documentCount: 19,
  findingCount: 10,
  auditEventCount: 4,
};

const userProject = {
  ...demoProject,
  projectId: "proj_user_abc123",
  projectName: "Maple Commons Stormwater Review",
  jurisdiction: "Town of Riverton",
  reviewType: "Site plan stormwater review",
  status: "intake_started",
  sourceMode: "user_created",
  createdByName: "Demo Reviewer",
  documentCount: 1,
  findingCount: 0,
  auditEventCount: 2,
};

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    listProjects: vi.fn(async () => [demoProject, userProject]),
    getProjectDetail: vi.fn(async () => userProject),
    listProjectDocuments: vi.fn(async () => [
      {
        documentId: "doc_user_1",
        projectId: userProject.projectId,
        fileName: "doc_abc.pdf",
        originalFileName: "Stormwater Report.pdf",
        documentType: "stormwater_report",
        status: "registered",
        purpose: "narrative",
        expectedKeyInformation: "",
        sourceMode: "user_registered",
        uploadStatus: "not_uploaded",
        processingStatus: "metadata_recorded",
        contentType: null,
        fileSizeBytes: null,
        checksumSha256: null,
        revisionLabel: "Rev A",
        revisionDate: null,
        uploadedByName: "Demo Reviewer",
        uploadedAt: null,
        registeredAt: "2026-06-26T00:00:00Z",
      },
    ]),
    listProjectFindings: vi.fn(async () => [
      {
        findingId: "find_user_1",
        projectId: userProject.projectId,
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
      },
    ]),
    listProjectAuditEvents: vi.fn(async () => [
      {
        auditEventId: "audit_1",
        projectId: userProject.projectId,
        eventType: "project_created",
        actorType: "reviewer",
        actorDisplayName: "Demo Reviewer",
        relatedEntityType: "project",
        relatedEntityId: userProject.projectId,
        description: "Reviewer created project record.",
        timestamp: "2026-06-26T00:00:00Z",
        eventMetadata: { source_mode: "user_created" },
      },
    ]),
  };
});

import ProjectsPage from "@/app/projects/page";
import NewProjectPage from "@/app/projects/new/page";
import ProjectDetailPage from "@/app/projects/[projectId]/page";
import ProjectDocumentsPage from "@/app/projects/[projectId]/documents/page";
import RegisterDocumentPage from "@/app/projects/[projectId]/documents/register/page";
import ProjectFindingsPage from "@/app/projects/[projectId]/findings/page";
import NewFindingPage from "@/app/projects/[projectId]/findings/new/page";
import ProjectAuditEventsPage from "@/app/projects/[projectId]/audit-events/page";

const params = Promise.resolve({ projectId: "proj_user_abc123" });

describe("Projects list page", () => {
  it("renders demo and user-created project rows with source badges", async () => {
    render(await ProjectsPage());
    expect(
      screen.getByText("Brookside Meadows Residential Subdivision"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Maple Commons Stormwater Review"),
    ).toBeInTheDocument();
    expect(screen.getByText("Demo fixture")).toBeInTheDocument();
    expect(screen.getByText("User-created")).toBeInTheDocument();
  });
});

describe("New project page", () => {
  it("renders the project intake form", async () => {
    render(NewProjectPage());
    expect(screen.getByText("Create project record")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Maple Commons/)).toBeInTheDocument();
  });
});

describe("Project detail page", () => {
  it("renders project metadata and counts", async () => {
    render(await ProjectDetailPage({ params }));
    expect(
      screen.getByText("Maple Commons Stormwater Review"),
    ).toBeInTheDocument();
    expect(screen.getByText("Town of Riverton")).toBeInTheDocument();
    // "Documents" and "Audit events" appear both as a metric label and a nav
    // link, so assert at least one of each is present.
    expect(screen.getAllByText("Documents").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Audit events").length).toBeGreaterThan(0);
  });
});

describe("Project documents page", () => {
  it("renders registered documents", async () => {
    render(await ProjectDocumentsPage({ params }));
    expect(screen.getByText("Stormwater Report.pdf")).toBeInTheDocument();
    expect(screen.getByText("metadata_recorded")).toBeInTheDocument();
  });
});

describe("Document registration page", () => {
  it("renders the document registration form", async () => {
    render(await RegisterDocumentPage({ params }));
    expect(screen.getByText("Register metadata")).toBeInTheDocument();
    // "Register document" is both the page title and the form submit button.
    expect(screen.getAllByText("Register document").length).toBeGreaterThan(0);
  });
});

describe("Reviewer findings page", () => {
  it("renders reviewer-created findings", async () => {
    render(await ProjectFindingsPage({ params }));
    expect(
      screen.getByText("Detention basin outlet detail missing"),
    ).toBeInTheDocument();
    expect(screen.getByText("reviewer_created")).toBeInTheDocument();
  });
});

describe("New finding page", () => {
  it("renders the reviewer finding form", async () => {
    render(await NewFindingPage({ params }));
    expect(
      screen.getByText("Create review-support finding"),
    ).toBeInTheDocument();
    // The boundary note appears in both the page header and the form body.
    expect(
      screen.getAllByText(
        /review-support finding requiring human confirmation/i,
      ).length,
    ).toBeGreaterThan(0);
  });
});

describe("Audit events page", () => {
  it("renders audit events with actor attribution", async () => {
    render(await ProjectAuditEventsPage({ params }));
    expect(screen.getByText("project_created")).toBeInTheDocument();
    expect(screen.getAllByText("Demo Reviewer").length).toBeGreaterThan(0);
  });
});

describe("Professional boundary in new UI", () => {
  it("uses no prohibited final-decision wording", async () => {
    const { container: c1 } = render(await ProjectDetailPage({ params }));
    const { container: c2 } = render(await NewFindingPage({ params }));
    const { container: c3 } = render(await RegisterDocumentPage({ params }));
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

describe("API base URL documentation", () => {
  it("never includes /api/v1 in NEXT_PUBLIC_API_BASE_URL examples", () => {
    const root = path.resolve(__dirname, "..", "..");
    for (const file of [".env.example", "README.md"]) {
      const contents = fs.readFileSync(path.join(root, file), "utf-8");
      // Only check assignment-style examples (VAR=value), not explanatory prose
      // that may legitimately mention the /api/v1 path the client appends.
      const lines = contents
        .split("\n")
        .filter((l) => /NEXT_PUBLIC_API_BASE_URL\s*=/.test(l));
      expect(lines.length).toBeGreaterThan(0);
      for (const line of lines) {
        expect(line).not.toContain("/api/v1");
      }
    }
  });
});
