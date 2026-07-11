import { ok } from "@/lib/api/__tests__/testHelpers";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

const projectId = "proj_user_1";

const project = {
  projectId,
  projectName: "Phase 3C Project",
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

const itemHigh = {
  workflowItemId: "wi_high",
  projectId,
  packetId: null,
  packetItemId: null,
  title: "High severity outlet item",
  description: "",
  sourceType: "cad_finding",
  sourceId: "cadf_1",
  severity: "high",
  status: "draft",
  assignedRole: "stormwater_reviewer",
  reviewerNote: null,
  targetDate: null,
  sectionType: "stormwater",
  evidenceTypes: [],
  requiresHumanReview: true,
  createdAt: "2026-06-28T00:00:00Z",
  updatedAt: "2026-06-28T00:00:00Z",
};

const itemLow = {
  ...itemHigh,
  workflowItemId: "wi_low",
  title: "Low severity grading item",
  severity: "low",
  sourceType: "checklist",
  requiresHumanReview: false,
};

const workflowSummary = {
  projectId,
  totalItems: 2,
  itemsByStatus: { draft: 2 },
  itemsBySeverity: { high: 1, low: 1 },
  itemsBySectionType: { stormwater: 2 },
  itemsByAssignedRole: { stormwater_reviewer: 2 },
  itemsRequiringHumanReview: 1,
  openFollowUpCount: 0,
  readyForHandoffCount: 0,
  note: "Review-support work items only.",
};

const handoffSummary = {
  projectId,
  totalItems: 2,
  readyCount: 0,
  outstandingFollowUpCount: 0,
  items: [],
  note: "Ready for handoff means organized for human review.",
};

const planSheet = {
  sheetId: "sheet_1",
  projectId,
  sheetNumber: "C-3",
  sheetTitle: "Grading and drainage plan",
  discipline: "civil",
  revision: "2",
  revisionDate: null,
  status: "received",
  fileName: null,
  sheetPurpose: "Grading",
  relatedDocuments: ["doc_1"],
  relatedChecklistItems: [],
  relatedFindings: [],
};

const planSummary = {
  projectId,
  totalSheets: 1,
  presentSheets: 1,
  missingOrReferencedNotIncluded: 0,
  needsReviewerConfirmation: 0,
  sheetsWithRelatedFindings: 0,
  cadMetadataRecords: 2,
  sheetsByDiscipline: { civil: 1 },
  missingSheetIds: [],
};

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDetail: vi.fn(async () => ok(project)),
    getWorkflowItems: vi.fn(async () => ok([itemHigh, itemLow])),
    getWorkflowBoardSummary: vi.fn(async () => ok(workflowSummary)),
    getReadyForHandoffSummary: vi.fn(async () => ok(handoffSummary)),
    getWorkflowItem: vi.fn(async () => ok(({
      ...itemHigh,
      evidenceLinks: [],
      followUps: [],
      actions: [],
    }))),
    getPlanSheets: vi.fn(async () => ok([planSheet])),
    getPlanSheetSummary: vi.fn(async () => ok(planSummary)),
  };
});

import WorkflowBoardClient from "@/components/WorkflowBoardClient";
import PlanSheetIndexPage from "@/app/projects/[projectId]/plan-sheets/page";

afterEach(() => cleanup());

describe("Workflow board filters", () => {
  it("renders filter controls and narrows items, then resets", async () => {
    render(<WorkflowBoardClient projectId={projectId} />);
    await waitFor(() =>
      expect(
        screen.getAllByText("High severity outlet item").length,
      ).toBeGreaterThan(0),
    );
    // No-filter state shows both items (grouped columns).
    expect(screen.getByText("Low severity grading item")).toBeInTheDocument();

    // Filter by severity narrows the displayed items.
    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "high" },
    });
    await waitFor(() =>
      expect(
        screen.queryByText("Low severity grading item"),
      ).not.toBeInTheDocument(),
    );
    expect(
      screen.getAllByText("High severity outlet item").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/filter\(s\) applied/i)).toBeInTheDocument();

    // Reset restores all items.
    fireEvent.click(screen.getByText("Reset filters"));
    await waitFor(() =>
      expect(
        screen.getByText("Low severity grading item"),
      ).toBeInTheDocument(),
    );
  });

  it("shows an honest no-match message that does not imply completeness", async () => {
    render(<WorkflowBoardClient projectId={projectId} />);
    await waitFor(() =>
      expect(
        screen.getAllByText("High severity outlet item").length,
      ).toBeGreaterThan(0),
    );
    fireEvent.change(screen.getByLabelText("Section type"), {
      target: { value: "stormwater" },
    });
    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "high" },
    });
    fireEvent.change(screen.getByLabelText("Requires human review"), {
      target: { value: "no" },
    });
    await waitFor(() =>
      expect(
        screen.getByText(/No items match the current filters/i),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByText(/not a statement that the project is\s*complete/i),
    ).toBeInTheDocument();
  });
});

describe("Plan sheet index page", () => {
  it("renders sheet metadata and links to detail", async () => {
    render(await PlanSheetIndexPage({ params: Promise.resolve({ projectId }) }));
    expect(screen.getByText("Plan sheets")).toBeInTheDocument();
    expect(screen.getByText("Grading and drainage plan")).toBeInTheDocument();
    const link = screen.getByText("C-3").closest("a");
    expect(link).toHaveAttribute(
      "href",
      `/projects/${projectId}/plan-sheets/sheet_1`,
    );
  });

  it("shows an honest empty state when no sheets exist", async () => {
    const api = await import("@/lib/api");
    (api.getPlanSheets as ReturnType<typeof vi.fn>).mockResolvedValueOnce(ok([]));
    (api.getPlanSheetSummary as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      kind: "not_found",
      message: "No summary yet.",
      retryable: false,
    });
    render(await PlanSheetIndexPage({ params: Promise.resolve({ projectId }) }));
    expect(screen.getByText("No plan sheets available")).toBeInTheDocument();
  });
});
