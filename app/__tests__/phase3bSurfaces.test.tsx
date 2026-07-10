import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

const BANNED = [
  "approved",
  "certified",
  "validated",
  "verified",
  "compliant",
  "passes review",
  "meets all requirements",
];

const projectId = "proj_user_1";

const project = {
  projectId,
  projectName: "Surfaces Project",
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

const cadDashboard = {
  projectId,
  totalFiles: 2,
  filesNeedingParse: 1,
  filesWithParseFailures: 0,
  parseRunsNeedingHumanReview: 1,
  totalFindings: 3,
  unpromotedFindingsCount: 1,
  promotedFindingsCount: 2,
  queueStatusCounts: { queued: 1 },
  validationStatusCounts: { accepted: 2 },
  parseStatusCounts: { parsed: 1 },
  limitationsNote: "Review-support CAD intake only.",
};

const unpromotedFinding = {
  cadReviewFindingId: "cadf_1",
  parseRunId: "run_1",
  cadFileId: "cad_1",
  projectId,
  findingType: "missing_referenced_sheet",
  title: "Referenced sheet C-4 not found",
  description: "A detail references sheet C-4 which is not present.",
  severity: "medium",
  sourceReferenceCandidateId: null,
  sourceLayerExtractId: null,
  sourceTextExtractId: null,
  linkedPlanSheetId: null,
  linkedWorkflowItemId: null,
  promotedToWorkflow: false,
  promotedWorkflowItemId: null,
  status: "open",
  requiresHumanReview: true,
  createdAt: "2026-06-28T00:00:00Z",
};

const workflowItem = {
  workflowItemId: "wi_1",
  projectId,
  packetId: null,
  packetItemId: null,
  title: "Detention basin outlet follow-up",
  description: "Reviewer follow-up on outlet sizing.",
  sourceType: "cad_finding",
  sourceId: "cadf_2",
  severity: "medium",
  status: "open",
  assignedRole: "stormwater_reviewer",
  reviewerNote: null,
  targetDate: null,
  sectionType: "stormwater",
  evidenceTypes: [],
  requiresHumanReview: true,
  createdAt: "2026-06-28T00:00:00Z",
  updatedAt: "2026-06-28T00:00:00Z",
};

const workflowSummary = {
  projectId,
  totalItems: 1,
  itemsByStatus: { open: 1 },
  itemsBySeverity: { medium: 1 },
  itemsBySectionType: { stormwater: 1 },
  itemsByAssignedRole: { stormwater_reviewer: 1 },
  itemsRequiringHumanReview: 1,
  openFollowUpCount: 0,
  readyForHandoffCount: 0,
  note: "Review-support work items only.",
};

const handoffSummary = {
  projectId,
  totalItems: 1,
  readyCount: 0,
  outstandingFollowUpCount: 0,
  items: [],
  note: "Ready for handoff means organized for human review, not complete.",
};

const sheetContext = {
  sheet: {
    sheetId: "sheet_1",
    projectId,
    sheetNumber: "C-3",
    sheetTitle: "Grading and drainage plan",
    discipline: "civil",
    revision: "2",
    revisionDate: "2026-06-01",
    status: "received",
    fileName: "C-3.pdf",
    sheetPurpose: "Grading and drainage",
    relatedDocuments: [],
    relatedChecklistItems: [],
    relatedFindings: [],
  },
  hotspots: [],
  cadMetadata: [],
  planReferences: [],
  planConsistencyFindings: [],
  previewNote: "No drawing preview is generated. This is review-support metadata only.",
};

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDetail: vi.fn(async () => project),
    // CAD
    getCadFiles: vi.fn(async () => []),
    getCadUploadLimits: vi.fn(async () => null),
    getCadIntakeDashboard: vi.fn(async () => cadDashboard),
    getCadParseQueue: vi.fn(async () => []),
    getUnpromotedCadFindings: vi.fn(async () => [unpromotedFinding]),
    getCadReviewFindings: vi.fn(async () => []),
    // Workflow
    getWorkflowItems: vi.fn(async () => [workflowItem]),
    getWorkflowBoardSummary: vi.fn(async () => workflowSummary),
    getReadyForHandoffSummary: vi.fn(async () => handoffSummary),
    getWorkflowItem: vi.fn(async () => ({
      ...workflowItem,
      evidenceLinks: [],
      followUps: [],
      actions: [],
    })),
    // Review packets
    getReviewPackets: vi.fn(async () => []),
    // Plan sheet
    getSheetViewerContext: vi.fn(async () => sheetContext),
    // Command center fallback
    getProjectCommandCenter: vi.fn(async () => null),
    getProjectHealthSummary: vi.fn(async () => null),
  };
});

import ProjectCadPage from "@/app/projects/[projectId]/cad/page";
import ProjectWorkflowBoardPage from "@/app/projects/[projectId]/workflow-board/page";
import ProjectReviewPacketsPage from "@/app/projects/[projectId]/review-packets/page";
import PlanSheetDetailPage from "@/app/projects/[projectId]/plan-sheets/[sheetId]/page";
import ProjectDashboard from "@/components/ProjectDashboard";

afterEach(() => cleanup());

describe("Project CAD page", () => {
  it("renders dashboard data, limitations note, and unpromoted promotion action", async () => {
    render(await ProjectCadPage({ params: Promise.resolve({ projectId }) }));
    expect(screen.getByText("CAD intake and metadata")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("Uploaded CAD files")).toBeInTheDocument(),
    );
    expect(
      screen.getAllByText(/does not verify CAD/i).length,
    ).toBeGreaterThan(0);
    await waitFor(() =>
      expect(
        screen.getByText("Referenced sheet C-4 not found"),
      ).toBeInTheDocument(),
    );
    expect(screen.getAllByText("Promote to workflow").length).toBeGreaterThan(0);
  });

  it("introduces no banned wording", async () => {
    const { container } = render(await ProjectCadPage({ params: Promise.resolve({ projectId }) }));
    await waitFor(() =>
      expect(screen.getByText("Uploaded CAD files")).toBeInTheDocument(),
    );
    const text = (container.textContent ?? "").toLowerCase();
    for (const word of BANNED) expect(text).not.toContain(word);
  });
});

describe("Project workflow board page", () => {
  it("renders the summary and grouped items", async () => {
    render(await ProjectWorkflowBoardPage({ params: Promise.resolve({ projectId }) }));
    expect(screen.getByText("Workflow board")).toBeInTheDocument();
    await waitFor(() =>
      expect(
        screen.getAllByText("Detention basin outlet follow-up").length,
      ).toBeGreaterThan(0),
    );
  });
});

describe("Project review packets page", () => {
  it("renders an honest empty state with a generate action", async () => {
    render(await ProjectReviewPacketsPage({ params: Promise.resolve({ projectId }) }));
    expect(screen.getByText("Review packets")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("Generate review packet")).toBeInTheDocument(),
    );
  });
});

describe("Project plan sheet page", () => {
  it("renders real sheet metadata when available", async () => {
    render(
      await PlanSheetDetailPage({
        params: Promise.resolve({ projectId, sheetId: "sheet_1" }),
      }),
    );
    expect(screen.getByText("Sheet metadata")).toBeInTheDocument();
    expect(screen.getByText("Grading and drainage plan")).toBeInTheDocument();
    expect(
      screen.getByText(/No drawing preview is rendered here/i),
    ).toBeInTheDocument();
  });

  it("shows an honest unavailable state when the sheet is not found", async () => {
    const api = await import("@/lib/api");
    (api.getSheetViewerContext as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      null,
    );
    render(
      await PlanSheetDetailPage({
        params: Promise.resolve({ projectId, sheetId: "missing" }),
      }),
    );
    expect(
      screen.getByText("Sheet metadata is unavailable"),
    ).toBeInTheDocument();
  });
});

describe("Command center fallback copy", () => {
  it("is project-neutral when the backend is unavailable", async () => {
    render(<ProjectDashboard projectId={projectId} />);
    await waitFor(() =>
      expect(
        screen.getByText(/The command center is unavailable/i),
      ).toBeInTheDocument(),
    );
    const body = document.body.textContent ?? "";
    expect(body).not.toContain("Brookside");
    expect(body).toMatch(/this project/i);
  });
});
