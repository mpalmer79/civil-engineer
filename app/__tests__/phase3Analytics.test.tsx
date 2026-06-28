import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

// Banned final-decision status/badge/CTA wording for pages authored in this
// pass. Negative boundary disclaimers use base verbs (approve, certify) which
// are intentionally not in this list.
const BANNED = [
  "approved",
  "certified",
  "validated",
  "verified",
  "compliant",
  "passes review",
  "meets all requirements",
];

const project = {
  projectId: "proj_user_1",
  projectName: "Analytics Project",
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

const planSummary = {
  projectId: "proj_user_1",
  totalSheets: 12,
  missingSheetCount: 1,
  cadMetadataRecords: 5,
  totalPlanReferences: 8,
  inconsistentReferences: 2,
  planConsistencyFindings: 3,
  conflictingLabelCount: 1,
  missingReferencedSheetCount: 1,
  missingPlanReferenceCount: 1,
  unclearRevisionCount: 0,
  requiresHumanReviewCount: 2,
  findingsRequiringHumanReview: 2,
};

const planFinding = {
  planFindingId: "pf_1",
  projectId: "proj_user_1",
  findingType: "conflicting_label",
  title: "Sheet label conflict on C-3",
  summary: "Label C-3 appears on two different sheets.",
  riskLevel: "medium",
  status: "open",
  relatedSheetIds: ["sheet_1"],
  relatedDocumentIds: ["doc_1"],
  relatedChecklistItems: ["chk_1"],
  relatedCadMetadataIds: ["cad_1"],
  recommendedHumanAction: "Reviewer should confirm the correct sheet label.",
};

const ccSnapshot = {
  snapshotId: "snap_1",
  projectId: "proj_user_1",
  currentReviewCycleId: "cycle_1",
  generatedAt: "2026-06-28T00:00:00Z",
  overallStatus: "active_review",
  summary: "Project is under review support with two attention items.",
  attentionCount: 2,
  readyForHandoffCount: 0,
  carryForwardCount: 0,
  needsMoreInformationCount: 1,
  cadFindingsCount: 0,
  resubmittalCount: 0,
  openFollowUpCount: 1,
  responseMappingGapCount: 0,
  revisionChangeCount: 0,
  requiresHumanReview: true,
};

const ccPayload = {
  snapshot: ccSnapshot,
  healthMetrics: [],
  attentionItems: [],
  timeline: [],
  readinessChecks: [],
  nextSteps: { projectId: "proj_user_1", snapshotId: "snap_1", steps: [], note: "" },
  moduleLinks: { projectId: "proj_user_1", links: [], note: "" },
  reviewerNotes: [],
  limitationsNote: "Review-support only. Not a final engineering decision.",
};

const healthSummary = {
  projectId: "proj_user_1",
  snapshotId: "snap_1",
  overallStatus: "active_review",
  currentReviewCycleId: "cycle_1",
  attentionCount: 2,
  readyForHandoffCount: 0,
  carryForwardCount: 0,
  needsMoreInformationCount: 1,
  cadFindingsCount: 0,
  resubmittalCount: 0,
  openFollowUpCount: 1,
  responseMappingGapCount: 0,
  revisionChangeCount: 0,
  readinessReadyCount: 0,
  summary: "Review-support health summary.",
  limitationsNote: "Review-support only.",
};

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDetail: vi.fn(async () => project),
    getPlanConsistencySummary: vi.fn(async () => planSummary),
    getPlanConsistencyFindings: vi.fn(async () => [planFinding]),
    getPlanConsistencyReviewActions: vi.fn(async () => []),
    getProjectCommandCenter: vi.fn(async () => ccPayload),
    getProjectHealthSummary: vi.fn(async () => healthSummary),
  };
});

import PlanConsistencyPage from "@/app/projects/[projectId]/plan-consistency/page";
import ProjectCommandCenterPage from "@/app/projects/[projectId]/command-center/page";
import ProjectDetailPage from "@/app/projects/[projectId]/page";

const projectId = "proj_user_1";

afterEach(() => cleanup());

describe("Plan consistency page", () => {
  it("renders the page, summary counts, findings, action control, and boundary", async () => {
    render(await PlanConsistencyPage({ params: { projectId } }));
    expect(screen.getByText("Plan consistency")).toBeInTheDocument();
    // Summary counts.
    expect(screen.getByText("Total sheets")).toBeInTheDocument();
    expect(screen.getByText("CAD metadata records")).toBeInTheDocument();
    expect(screen.getByText("Inconsistent references")).toBeInTheDocument();
    // Finding card.
    expect(screen.getByText("Sheet label conflict on C-3")).toBeInTheDocument();
    expect(
      screen.getByText(/Reviewer should confirm the correct sheet label/),
    ).toBeInTheDocument();
    // Review action control is surfaced (backend supports it).
    expect(screen.getAllByText("Record action").length).toBeGreaterThan(0);
    // Boundary note visible.
    expect(
      screen.getByText(/potential issues for a human reviewer/i),
    ).toBeInTheDocument();
    // A related document id links to the document detail route (no dead link).
    const docLink = screen.getByText("doc_1").closest("a");
    expect(docLink).toHaveAttribute(
      "href",
      `/projects/${projectId}/documents/doc_1`,
    );
  });

  it("introduces no banned final-decision wording", async () => {
    const { container } = render(
      await PlanConsistencyPage({ params: { projectId } }),
    );
    const text = (container.textContent ?? "").toLowerCase();
    for (const word of BANNED) {
      expect(text).not.toContain(word);
    }
  });
});

describe("Command center page", () => {
  it("renders the snapshot, counts, boundary, and reviewer controls", async () => {
    render(await ProjectCommandCenterPage({ params: { projectId } }));
    expect(screen.getByText("Command center")).toBeInTheDocument();
    // ProjectDashboard loads asynchronously, then renders snapshot data.
    await waitFor(() =>
      expect(
        screen.getByText(
          /Project is under review support with two attention items/,
        ),
      ).toBeInTheDocument(),
    );
    // Boundary/limitations notice.
    expect(
      screen.getByText("Command center limitations"),
    ).toBeInTheDocument();
    // Regenerate snapshot control is wired.
    expect(screen.getByText("Refresh snapshot")).toBeInTheDocument();
  });
});

describe("Project navigation to analytical surfaces", () => {
  it("links to all touched routes without 404 targets", async () => {
    const { container } = render(
      await ProjectDetailPage({ params: { projectId } }),
    );
    const hrefs = Array.from(container.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    for (const route of [
      "command-center",
      "plan-consistency",
      "cad",
      "workflow-board",
      "review-packets",
    ]) {
      expect(hrefs).toContain(`/projects/${projectId}/${route}`);
    }
  });
});
