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
  "compliant",
  "noncompliant",
  "passed",
  "failed",
  "verified",
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
  projectName: "Checklist Project",
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

const rulePack = {
  rulePackId: "rulepack_starter",
  name: "Brookside Stormwater Review Starter Pack",
  jurisdictionName: "Starter template (no jurisdiction)",
  reviewDomain: "stormwater",
  description: "A reusable starter stormwater review checklist.",
  versionLabel: "v1",
  sourceMode: "seeded_demo",
  isActive: true,
  createdByName: "Seeded demo",
  createdAt: null,
  updatedAt: null,
  itemCount: 2,
  items: [
    {
      rulePackItemId: "rpi_do01",
      rulePackId: "rulepack_starter",
      itemCode: "DO-01",
      category: "Detention and outlet control",
      requirementText: "Detention storage and outlet control are sized.",
      expectedEvidence: "Stage storage table and outlet computations.",
      applicabilityNote: "Applies when detention is proposed.",
      riskLevel: "high",
      reviewDomain: "stormwater",
      referenceLabel: "Starter template, not ordinance",
      sortOrder: 0,
      isActive: true,
    },
    {
      rulePackItemId: "rpi_sc01",
      rulePackId: "rulepack_starter",
      itemCode: "SC-01",
      category: "Submission completeness",
      requirementText: "A complete submission package is provided.",
      expectedEvidence: "Cover sheet, drainage report, and index.",
      applicabilityNote: "Applies to all submissions.",
      riskLevel: "medium",
      reviewDomain: "stormwater",
      referenceLabel: "Starter template, not ordinance",
      sortOrder: 1,
      isActive: true,
    },
  ],
};

const checklist = {
  projectChecklistId: "pcl_1",
  projectId: "proj_user_1",
  rulePackId: "rulepack_starter",
  name: "Brookside Stormwater Review Starter Pack",
  status: "checklist_started",
  sourceMode: "user_created",
  createdByName: "Demo Reviewer",
  createdAt: null,
  updatedAt: null,
  itemCount: 2,
  evidenceStatusSummary: { not_reviewed: 2 },
  reviewStatusSummary: { not_started: 2 },
};

const checklistItem = {
  projectChecklistItemId: "pcli_1",
  projectChecklistId: "pcl_1",
  projectId: "proj_user_1",
  rulePackItemId: "rpi_do01",
  itemCode: "DO-01",
  category: "Detention and outlet control",
  requirementText: "Detention storage and outlet control are sized.",
  expectedEvidence: "Stage storage table and outlet computations.",
  applicabilityStatus: "needs_reviewer_confirmation",
  evidenceStatus: "not_reviewed",
  reviewStatus: "not_started",
  riskLevel: "high",
  reviewerNote: null,
  relatedFindingId: null,
  sortOrder: 0,
  reviewedByName: null,
  reviewedAt: null,
  createdAt: null,
  updatedAt: null,
};

const { createChecklistMock, updateItemMock, searchMock, draftMock } =
  vi.hoisted(() => ({
    createChecklistMock: vi.fn(),
    updateItemMock: vi.fn(),
    searchMock: vi.fn(),
    draftMock: vi.fn(),
  }));

beforeEach(() => {
  createChecklistMock.mockReset();
  updateItemMock.mockReset();
  searchMock.mockReset();
  draftMock.mockReset();
  createChecklistMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: checklist,
  });
  updateItemMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: { ...checklistItem, evidenceStatus: "missing_evidence" },
  });
  searchMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: {
      projectId: "proj_user_1",
      queryText: "detention basin",
      queryType: "checklist_item",
      retrievalQueryId: "rq_1",
      resultCount: 1,
      results: [
        {
          documentId: "doc_1",
          documentName: "Plan.pdf",
          documentType: "stormwater_report",
          documentPageId: "docpage_1",
          pageNumber: 1,
          pageLabel: "Page 1",
          textExtractionStatus: "text_extracted",
          excerpt: "...detention basin outlet...",
          matchTerms: ["detention"],
          rankingScore: 0.8,
          rankingReason: "Ranked by keyword match.",
          candidateOrigin: "checklist_search",
          retrievalQueryId: "rq_1",
        },
      ],
      message: "1 retrieval candidate(s) for reviewer review.",
    },
  });
  draftMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: {
      finding: {
        findingId: "find_checklist_1",
        projectId: "proj_user_1",
        title: "Draft",
        category: "Detention and outlet control",
        riskLevel: "high",
        evidenceStatus: "missing_evidence",
        humanReviewStatus: "draft",
        findingOrigin: "checklist_review",
        sourceMode: "user_created",
        relatedChecklistItems: ["pcli_1"],
        createdByName: "Demo Reviewer",
      },
      citation: null,
      checklistItem: { ...checklistItem, reviewStatus: "draft_finding_created" },
    },
  });
});

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDetail: vi.fn(async () => project),
    listRulePacks: vi.fn(async () => [rulePack]),
    getRulePack: vi.fn(async () => rulePack),
    listProjectChecklists: vi.fn(async () => [checklist]),
    getProjectChecklist: vi.fn(async () => checklist),
    listProjectChecklistItems: vi.fn(async () => [checklistItem]),
    createProjectChecklistFromRulePack: createChecklistMock,
    updateProjectChecklistItem: updateItemMock,
    searchChecklistItemEvidence: searchMock,
    createDraftFindingFromChecklistItem: draftMock,
  };
});

import RulePacksPage from "@/app/rule-packs/page";
import RulePackDetailPage from "@/app/rule-packs/[rulePackId]/page";
import ProjectChecklistsPage from "@/app/projects/[projectId]/checklists/page";
import ChecklistDetailPage from "@/app/projects/[projectId]/checklists/[checklistId]/page";
import ChecklistItemDetailPage from "@/app/projects/[projectId]/checklists/[checklistId]/items/[itemId]/page";
import ProjectDetailPage from "@/app/projects/[projectId]/page";
import CreateChecklistFromRulePack from "@/components/CreateChecklistFromRulePack";
import ChecklistItemReviewPanel from "@/components/ChecklistItemReviewPanel";

const projectId = "proj_user_1";
const checklistId = "pcl_1";

describe("Rule packs page", () => {
  it("renders the starter rule pack and the template note", async () => {
    render(await RulePacksPage());
    expect(
      screen.getByText("Brookside Stormwater Review Starter Pack"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/review-support templates, not legal determinations/i),
    ).toBeInTheDocument();
  });
});

describe("Rule pack detail page", () => {
  it("renders item categories and codes", async () => {
    render(
      await RulePackDetailPage({ params: { rulePackId: "rulepack_starter" } }),
    );
    expect(screen.getByText("Detention and outlet control")).toBeInTheDocument();
    expect(screen.getByText(/DO-01/)).toBeInTheDocument();
    expect(
      screen.getByText(/starter review template, not a legal ordinance/i),
    ).toBeInTheDocument();
  });
});

describe("Project checklists page", () => {
  it("renders existing checklists and the create panel", async () => {
    render(await ProjectChecklistsPage({ params: { projectId } }));
    expect(screen.getByText("Project checklists")).toBeInTheDocument();
    expect(
      screen.getByText("Create checklist from a rule pack"),
    ).toBeInTheDocument();
  });
});

describe("Create checklist from rule pack", () => {
  it("sends the expected payload", async () => {
    render(
      <CreateChecklistFromRulePack
        projectId={projectId}
        rulePacks={[
          {
            rulePackId: "rulepack_starter",
            name: "Starter Pack",
            itemCount: 16,
          },
        ]}
      />,
    );
    fireEvent.click(screen.getByText("Create checklist"));
    await waitFor(() => expect(createChecklistMock).toHaveBeenCalled());
    const call = createChecklistMock.mock.calls[0] as unknown as [
      string,
      { rulePackId: string },
    ];
    expect(call[0]).toBe(projectId);
    expect(call[1].rulePackId).toBe("rulepack_starter");
  });
});

describe("Checklist detail page", () => {
  it("groups checklist items by category", async () => {
    render(
      await ChecklistDetailPage({ params: { projectId, checklistId } }),
    );
    expect(screen.getByText("Detention and outlet control")).toBeInTheDocument();
    expect(screen.getByText(/DO-01/)).toBeInTheDocument();
    expect(screen.getByText("Not reviewed")).toBeInTheDocument();
  });
});

describe("Checklist item detail page", () => {
  it("renders requirement, expected evidence, statuses, and search panel", async () => {
    render(
      await ChecklistItemDetailPage({
        params: { projectId, checklistId, itemId: "pcli_1" },
      }),
    );
    expect(
      screen.getByText(/Stage storage table and outlet computations/),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Search evidence for this requirement"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Create draft finding from this item"),
    ).toBeInTheDocument();
  });
});

describe("Checklist item review panel", () => {
  it("searches evidence with the expected payload", async () => {
    render(
      <ChecklistItemReviewPanel projectId={projectId} item={checklistItem} />,
    );
    fireEvent.click(screen.getByText("Search checklist evidence"));
    await waitFor(() => expect(searchMock).toHaveBeenCalled());
    const call = searchMock.mock.calls[0] as unknown as [string, string];
    expect(call[0]).toBe(projectId);
    expect(call[1]).toBe("pcli_1");
    await waitFor(() => {
      expect(screen.getByText(/Plan.pdf, page 1/)).toBeInTheDocument();
    });
  });

  it("creates a draft finding with a safe evidence status payload", async () => {
    render(
      <ChecklistItemReviewPanel projectId={projectId} item={checklistItem} />,
    );
    fireEvent.click(screen.getByText("Create reviewer draft finding"));
    await waitFor(() => expect(draftMock).toHaveBeenCalled());
    const call = draftMock.mock.calls[0] as unknown as [
      string,
      string,
      { evidenceStatus: string },
    ];
    expect(call[2].evidenceStatus).toBe("missing_evidence");
  });
});

describe("Project overview links", () => {
  it("links to project checklists and rule packs", async () => {
    const { container } = render(
      await ProjectDetailPage({ params: { projectId } }),
    );
    const hrefs = Array.from(container.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    expect(hrefs).toContain(`/projects/${projectId}/checklists`);
    expect(hrefs).toContain("/rule-packs");
  });
});

describe("Professional boundary in new Sprint 4 UI", () => {
  it("uses no prohibited final-decision wording", async () => {
    const { container: c1 } = render(await RulePacksPage());
    const { container: c2 } = render(
      await ChecklistDetailPage({ params: { projectId, checklistId } }),
    );
    const { container: c3 } = render(
      <ChecklistItemReviewPanel projectId={projectId} item={checklistItem} />,
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
