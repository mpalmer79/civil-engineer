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

// These words must never appear as affirmative status. "satisfied" and "proven"
// are intentionally excluded: the page uses them only inside negative boundary
// statements ("does not determine whether a requirement is satisfied"), which is
// the one allowed use.
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
  projectName: "Phase 4 Project",
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

const traceability = {
  projectId,
  generatedAt: "2026-06-28T00:00:00Z",
  limitationsNote:
    "Review-support traceability. It does not determine whether a requirement is satisfied. Reviewer confirmation is required.",
  hasIndexedInformation: true,
  summary: {
    totalChecklistItems: 2,
    checklistItemsWithLinkedEvidence: 1,
    checklistItemsWithoutLinkedEvidence: 1,
    totalEvidenceCitations: 1,
    totalEvidenceCandidates: 0,
    totalFindings: 1,
    totalWorkflowItems: 1,
    totalPacketItems: 0,
    totalTraceabilityRows: 2,
    rowsRequiringReviewerConfirmation: 2,
  },
  rows: [
    {
      traceabilityRowId: "trace_1",
      checklistItemId: "ci_1",
      checklistTitle: "SW-1",
      checklistRequirement: "Detention basin outlet detail required.",
      checklistStatus: "not_started",
      evidenceCandidateId: null,
      evidenceCitationId: "cite_1",
      documentId: "doc_1",
      documentName: "Plan Set.pdf",
      documentPageId: "docpage_1",
      pageNumber: 2,
      citationExcerpt: "detention basin outlet",
      findingId: "find_1",
      findingTitle: "Outlet detail missing",
      findingStatus: "draft",
      workflowItemId: "wi_1",
      workflowItemTitle: "Outlet follow-up",
      workflowStatus: "draft",
      cadFindingId: null,
      planFindingId: null,
      planSheetId: null,
      reviewPacketId: null,
      reviewPacketItemId: null,
      relationshipType: "linked_evidence",
      relationshipSource: "evidence_citation",
      reviewerActionNeeded: true,
      sourceLinks: [
        { type: "document", id: "doc_1" },
        { type: "finding", id: "find_1" },
        { type: "review_packet", id: null },
      ],
      notes: "not_reviewed",
    },
    {
      traceabilityRowId: "trace_2",
      checklistItemId: "ci_2",
      checklistTitle: "SW-2",
      checklistRequirement: "Erosion control plan required.",
      checklistStatus: "not_started",
      evidenceCandidateId: null,
      evidenceCitationId: null,
      documentId: null,
      documentName: null,
      documentPageId: null,
      pageNumber: null,
      citationExcerpt: null,
      findingId: null,
      findingTitle: null,
      findingStatus: null,
      workflowItemId: null,
      workflowItemTitle: null,
      workflowStatus: null,
      cadFindingId: null,
      planFindingId: null,
      planSheetId: null,
      reviewPacketId: null,
      reviewPacketItemId: null,
      relationshipType: "no_linked_evidence_yet",
      relationshipSource: "checklist_item",
      reviewerActionNeeded: true,
      sourceLinks: [],
      notes: "no_linked_evidence_yet",
    },
  ],
};

const printView = {
  packetId: "pkt_1",
  projectId,
  title: "Stormwater review packet",
  packetType: "stormwater",
  status: "draft",
  summary: "Draft review-support packet.",
  generatedFromPhase: "phase_8",
  createdBy: "Town Engineer",
  createdAt: "2026-06-28T00:00:00Z",
  limitationsNote: "Review-support only.",
  professionalLimitations:
    "This packet does not approve plans or replace a licensed Professional Engineer.",
  draftNotice: "Draft handoff package. Requires reviewer confirmation.",
  sections: [],
};

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDetail: vi.fn(async () => project),
    getProjectTraceability: vi.fn(async () => traceability),
    getReviewPacketPrintView: vi.fn(async () => printView),
  };
});

import ProjectTraceabilityPage from "@/app/projects/[projectId]/traceability/page";
import ReviewPacketPrintPreview from "@/components/ReviewPacketPrintPreview";

afterEach(() => cleanup());

describe("Project traceability page", () => {
  it("renders summary tiles, limitations, and linked + no-linked rows", async () => {
    render(await ProjectTraceabilityPage({ params: { projectId } }));
    expect(screen.getByText("Traceability")).toBeInTheDocument();
    // Summary tiles.
    expect(screen.getByText("Checklist items")).toBeInTheDocument();
    expect(screen.getByText("With linked evidence")).toBeInTheDocument();
    expect(screen.getByText("No linked evidence yet")).toBeInTheDocument();
    // Limitations note (appears in the page description and the boundary note).
    expect(
      screen.getAllByText(
        /does not determine whether a requirement is satisfied/i,
      ).length,
    ).toBeGreaterThan(0);
    // Linked + unlinked rows.
    expect(screen.getByText("Outlet detail missing")).toBeInTheDocument();
    expect(screen.getAllByText(/no linked evidence yet/i).length).toBeGreaterThan(
      0,
    );
    // Source link resolves to a real route. "Document" also appears as a filter
    // label, so pick the one that is an anchor.
    const docLink = screen
      .getAllByText("Document")
      .map((el) => el.closest("a"))
      .find((a): a is HTMLAnchorElement => a !== null);
    expect(docLink).toHaveAttribute(
      "href",
      `/projects/${projectId}/documents/doc_1`,
    );
  });

  it("filters rows by relationship type", async () => {
    render(await ProjectTraceabilityPage({ params: { projectId } }));
    expect(screen.getByText("SW-2")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Relationship type"), {
      target: { value: "linked_evidence" },
    });
    await waitFor(() =>
      expect(screen.queryByText("SW-2")).not.toBeInTheDocument(),
    );
    expect(screen.getByText("SW-1")).toBeInTheDocument();
  });

  it("introduces no banned wording", async () => {
    const { container } = render(
      await ProjectTraceabilityPage({ params: { projectId } }),
    );
    const text = (container.textContent ?? "").toLowerCase();
    for (const word of BANNED) expect(text).not.toContain(word);
  });
});

describe("Reviewer handoff print preview", () => {
  it("renders draft notice, limitations, and a print action", async () => {
    render(<ReviewPacketPrintPreview packetId="pkt_1" />);
    await waitFor(() =>
      expect(
        screen.getByText("Reviewer handoff package (draft)"),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("Open print view")).toBeInTheDocument();
    expect(
      screen.getByText(/Draft handoff package. Requires reviewer confirmation/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not approve plans or replace a licensed/i),
    ).toBeInTheDocument();
  });
});
