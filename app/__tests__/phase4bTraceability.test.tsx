import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ProjectTraceabilityRow } from "@/lib/api";

// Banned final-decision wording that must never appear as a status, badge, CTA,
// or label. "satisfied"/"proven" are excluded: they appear only inside negative
// boundary statements elsewhere, not in these components.
const BANNED = [
  "approved",
  "certified",
  "validated",
  "verified",
  "compliant",
  "passes review",
  "meets all requirements",
];

const recordMock = vi.fn();
const historyMock = vi.fn();

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    recordTraceabilityReviewAction: (...args: unknown[]) => recordMock(...args),
    getTraceabilityReviewActions: (...args: unknown[]) => historyMock(...args),
  };
});

import TraceabilityMatrix from "@/components/TraceabilityMatrix";
import ReviewPacketPrintPreview from "@/components/ReviewPacketPrintPreview";

const projectId = "proj_user_1";

function makeRow(overrides: Partial<ProjectTraceabilityRow>): ProjectTraceabilityRow {
  return {
    traceabilityRowId: "trace_1",
    traceabilityRowKey: "trk_1",
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
    workflowItemId: null,
    workflowItemTitle: null,
    workflowStatus: null,
    cadFindingId: null,
    planFindingId: null,
    planSheetId: null,
    reviewPacketId: null,
    reviewPacketItemId: null,
    relationshipType: "linked_evidence",
    relationshipSource: "evidence_citation",
    reviewerActionNeeded: true,
    sourceLinks: [{ type: "document", id: "doc_1" }],
    packetContexts: [],
    packetContextCount: 0,
    latestReviewAction: null,
    notes: "not_reviewed",
    ...overrides,
  };
}

const linkedRow = makeRow({
  packetContexts: [
    {
      reviewPacketId: "pkt_1",
      reviewPacketTitle: "Stormwater review packet",
      reviewPacketItemId: "item_1",
      reviewPacketSectionId: "sec_1",
      reviewPacketSectionTitle: "Document and checklist findings",
      packetItemStatus: "draft",
      packetItemSource: "finding",
      packetTraceabilityRelationship: "checklist_item",
      packetSourceLink: { type: "review_packet", id: "pkt_1" },
    },
  ],
  packetContextCount: 1,
});

const unlinkedRow = makeRow({
  traceabilityRowId: "trace_2",
  traceabilityRowKey: "trk_2",
  checklistItemId: "ci_2",
  checklistTitle: "SW-2",
  checklistRequirement: "Erosion control plan required.",
  evidenceCitationId: null,
  documentId: null,
  documentName: null,
  documentPageId: null,
  pageNumber: null,
  citationExcerpt: null,
  findingId: null,
  findingTitle: null,
  findingStatus: null,
  relationshipType: "no_linked_evidence_yet",
  relationshipSource: "checklist_item",
  sourceLinks: [],
  notes: "no_linked_evidence_yet",
});

afterEach(() => {
  cleanup();
  recordMock.mockReset();
  historyMock.mockReset();
});

describe("Traceability matrix packet context and review controls", () => {
  it("renders inline packet context and an honest no-packet state", () => {
    render(
      <TraceabilityMatrix projectId={projectId} rows={[linkedRow, unlinkedRow]} />,
    );
    // Packet context for the linked row links to review packets.
    const packetLink = screen.getByText("Stormwater review packet").closest("a");
    expect(packetLink).toHaveAttribute(
      "href",
      `/projects/${projectId}/review-packets`,
    );
    // The unlinked row is honest about packet inclusion.
    expect(
      screen.getAllByText("not included in a packet yet").length,
    ).toBeGreaterThan(0);
  });

  it("renders reviewer controls and submits an action to the backend", async () => {
    recordMock.mockResolvedValue({
      ok: true,
      status: 201,
      backendReachable: true,
      action: {
        actionId: "trace_act_1",
        projectId,
        traceabilityRowKey: "trk_1",
        actionType: "reviewer_confirmed_link",
        reviewerNote: "Useful for review.",
        createdBy: "Town Engineer",
        relationshipType: "linked_evidence",
        createdAt: "2026-06-28T00:00:00Z",
      },
    });

    render(<TraceabilityMatrix projectId={projectId} rows={[linkedRow]} />);

    // Before any action the row requires reviewer confirmation.
    expect(
      screen.getByText("requires reviewer confirmation"),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Review action for SW-1"), {
      target: { value: "reviewer_confirmed_link" },
    });
    fireEvent.change(screen.getByLabelText("Reviewer note for SW-1"), {
      target: { value: "Useful for review." },
    });
    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => expect(recordMock).toHaveBeenCalledTimes(1));
    const [, rowKey, input] = recordMock.mock.calls[0];
    expect(rowKey).toBe("trk_1");
    expect(input.actionType).toBe("reviewer_confirmed_link");
    expect(input.checklistItemId).toBe("ci_1");

    // The latest action appears after submit: the note shows and the
    // requires-confirmation prompt is gone.
    await waitFor(() =>
      expect(screen.getByText(/Useful for review\./)).toBeInTheDocument(),
    );
    expect(
      screen.queryByText("requires reviewer confirmation"),
    ).not.toBeInTheDocument();
  });

  it("keeps source data visible after a link is rejected", async () => {
    recordMock.mockResolvedValue({
      ok: true,
      status: 201,
      backendReachable: true,
      action: {
        actionId: "trace_act_2",
        projectId,
        traceabilityRowKey: "trk_1",
        actionType: "link_rejected",
        reviewerNote: null,
        createdBy: "reviewer",
        relationshipType: "linked_evidence",
        createdAt: "2026-06-28T00:00:00Z",
      },
    });

    render(<TraceabilityMatrix projectId={projectId} rows={[linkedRow]} />);
    fireEvent.change(screen.getByLabelText("Review action for SW-1"), {
      target: { value: "link_rejected" },
    });
    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => expect(recordMock).toHaveBeenCalledTimes(1));
    expect(recordMock.mock.calls[0][2].actionType).toBe("link_rejected");
    // The row no longer prompts for confirmation, but its source data remains.
    await waitFor(() =>
      expect(
        screen.queryByText("requires reviewer confirmation"),
      ).not.toBeInTheDocument(),
    );
    expect(screen.getByText("Plan Set.pdf")).toBeInTheDocument();
    expect(
      screen.getAllByText(/detention basin outlet/i).length,
    ).toBeGreaterThan(0);
  });

  it("introduces no banned wording", () => {
    const { container } = render(
      <TraceabilityMatrix projectId={projectId} rows={[linkedRow, unlinkedRow]} />,
    );
    const text = (container.textContent ?? "").toLowerCase();
    for (const word of BANNED) expect(text).not.toContain(word);
  });
});

describe("Review packet handoff traceability state", () => {
  const printView = {
    packetId: "pkt_1",
    projectId,
    title: "Stormwater review packet",
    packetType: "review_support_draft",
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
    traceabilityReviewRows: [
      {
        traceabilityRowKey: "trk_1",
        checklistTitle: "SW-1",
        checklistRequirement: "Detention basin outlet detail required.",
        relationshipType: "linked_evidence",
        reviewActionType: "reviewer_confirmed_link",
        reviewerNote: "Useful for review.",
        createdBy: "Town Engineer",
        requiresReviewerConfirmation: false,
      },
      {
        traceabilityRowKey: "trk_2",
        checklistTitle: "SW-2",
        checklistRequirement: "Erosion control plan required.",
        relationshipType: "no_linked_evidence_yet",
        reviewActionType: null,
        reviewerNote: null,
        createdBy: null,
        requiresReviewerConfirmation: true,
      },
    ],
    traceabilityNote: "Traceability review state for rows included in this packet.",
  };

  it("renders traceability review state and keeps draft notice and limitations", async () => {
    const api = await import("@/lib/api");
    vi.spyOn(api, "getReviewPacketPrintView").mockResolvedValue({
      ok: true,
      data: printView,
      source: "backend",
      status: 200,
    });

    render(<ReviewPacketPrintPreview packetId="pkt_1" />);

    await waitFor(() =>
      expect(
        screen.getByText("Traceability review state"),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("Confirmed link for review")).toBeInTheDocument();
    // A row with no action is honest about needing confirmation.
    expect(
      screen.getByText("requires reviewer confirmation"),
    ).toBeInTheDocument();
    // Draft notice and professional limitations remain visible.
    expect(
      screen.getByText(/Draft handoff package. Requires reviewer confirmation/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not approve plans or replace a licensed/i),
    ).toBeInTheDocument();
    // Link to project traceability is available.
    const link = screen.getByText("Open project traceability").closest("a");
    expect(link).toHaveAttribute("href", `/projects/${projectId}/traceability`);
  });
});
