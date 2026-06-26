import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const refreshMock = vi.fn();
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "compliant",
  "noncompliant",
  "passed review",
  "failed review",
  "verified",
  "validated",
  "resolved",
  "closed",
];

const FORBIDDEN_LEAKS = [
  "storage_path",
  "storage_key",
  "signed_url",
  "secret",
  "password",
  "token",
  "/var/",
];

const BOUNDARY =
  "This response package is prepared for reviewer support. It does not approve plans, certify compliance, verify design, validate CAD, declare safety, resolve issues, close issues, or replace the judgment of a licensed Professional Engineer.";
const LETTER_BOUNDARY =
  "This draft is prepared for reviewer support. It does not approve plans, certify compliance, verify design, validate CAD, declare safety, resolve issues, close issues, or replace the judgment of a licensed Professional Engineer.";

const project = {
  projectId: "proj_1",
  projectName: "Brookside Meadows",
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
  sourceMode: "demo_fixture",
  createdByName: "Seeded demo",
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
  auditEventCount: 1,
};

const pkg = {
  responsePackageId: "rpkg_1",
  projectId: "proj_1",
  responseMatrixId: null,
  resubmittalRoundId: null,
  packageTitle: "Initial review comments",
  packageNumber: 1,
  revisionNumber: 0,
  status: "package_in_review",
  packageType: "initial_review_comment_letter",
  sourceMode: "user_created",
  preparedByName: "Demo Reviewer",
  issuedByName: null,
  issuedAt: null,
  createdAt: null,
  updatedAt: null,
  itemCount: 1,
  includedItemCount: 1,
  items: [
    {
      responsePackageItemId: "rpi_1",
      responsePackageId: "rpkg_1",
      projectId: "proj_1",
      sourceType: "finding",
      sourceFindingId: "find_1",
      sourceChecklistItemId: null,
      sourceMatrixItemId: null,
      sourceCitationId: null,
      sourceDocumentId: null,
      itemNumber: "1",
      category: "stormwater",
      reviewerCommentText: "Provide the detention outlet detail.",
      applicantResponseSummary: null,
      reviewerFollowUpText: null,
      requestedEvidence: "Outlet sizing detail",
      citationReference: null,
      includeInLetter: true,
      sortOrder: 0,
      itemStatus: "item_draft",
      createdByName: "Demo Reviewer",
      updatedByName: null,
      createdAt: null,
      updatedAt: null,
    },
  ],
};

const finding = {
  findingId: "find_1",
  projectId: "proj_1",
  title: "Detention basin outlet needs reviewer confirmation",
  category: "stormwater",
  riskLevel: "medium",
  evidenceStatus: null,
  evidenceToFind: "Outlet detail",
  reasonItMatters: "Capacity",
  recommendedHumanAction: "Reviewer confirms",
  humanReviewStatus: "draft",
  relatedDocuments: [],
  relatedChecklistItems: [],
  sourceMode: "user_created",
};

const preview = {
  responsePackageId: "rpkg_1",
  projectId: "proj_1",
  projectName: "Brookside Meadows",
  packageTitle: "Initial review comments",
  packageType: "initial_review_comment_letter",
  packageNumber: 1,
  revisionNumber: 0,
  status: "package_in_review",
  issuedByName: null,
  issuedAt: null,
  boundaryStatement: BOUNDARY,
  itemCount: 1,
  items: [
    {
      itemNumber: "1",
      category: "stormwater",
      reviewerCommentText: "Provide the detention outlet detail.",
      requestedEvidence: "Outlet sizing detail",
      applicantResponseSummary: null,
      reviewerFollowUpText: null,
      citationReference: null,
      itemStatus: "item_draft",
    },
  ],
};

const draft = {
  commentLetterDraftId: "cldraft_1",
  responsePackageId: "rpkg_1",
  projectId: "proj_1",
  title: "Initial review comments comment letter draft",
  recipientName: "Design Firm",
  recipientOrganization: null,
  subjectLine: "Stormwater review comments: Brookside Meadows",
  introductionText: "Intro text",
  projectSummaryText: "Project summary",
  reviewScopeText: "Review scope",
  commentItemsText: "Comment 1\nReviewer comment: Provide the detention outlet detail.",
  resubmittalSummaryText: null,
  closingText: "Closing text",
  status: "draft_created",
  revisionNumber: 0,
  boundaryStatement: LETTER_BOUNDARY,
  createdByName: "Demo Reviewer",
  createdAt: null,
  updatedAt: null,
};

const letterPreview = {
  commentLetterDraftId: "cldraft_1",
  responsePackageId: "rpkg_1",
  projectId: "proj_1",
  title: "Initial review comments comment letter draft",
  recipientName: "Design Firm",
  recipientOrganization: null,
  status: "draft_created",
  revisionNumber: 0,
  boundaryStatement: LETTER_BOUNDARY,
  sections: [
    { heading: "Introduction", body: "Intro text" },
    { heading: "Review-support comments", body: "Comment 1" },
  ],
};

const {
  createPackageMock,
  addFindingsMock,
  issueMock,
  revisionMock,
  generateLetterMock,
  updateLetterMock,
  updateItemMock,
  readyMock,
} = vi.hoisted(() => ({
  createPackageMock: vi.fn(),
  addFindingsMock: vi.fn(),
  issueMock: vi.fn(),
  revisionMock: vi.fn(),
  generateLetterMock: vi.fn(),
  updateLetterMock: vi.fn(),
  updateItemMock: vi.fn(),
  readyMock: vi.fn(),
}));

beforeEach(() => {
  refreshMock.mockReset();
  pushMock.mockReset();
  for (const m of [
    createPackageMock,
    addFindingsMock,
    issueMock,
    revisionMock,
    generateLetterMock,
    updateLetterMock,
    updateItemMock,
    readyMock,
  ]) {
    m.mockReset();
    m.mockResolvedValue({ ok: true, backendReachable: true, data: pkg });
  }
  generateLetterMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: draft,
  });
  updateLetterMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: draft,
  });
});

afterEach(() => cleanup());

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectDetail: vi.fn(async () => project),
    listResponsePackages: vi.fn(async () => [pkg]),
    getResponsePackageDetail: vi.fn(async () => pkg),
    listProjectFindings: vi.fn(async () => [finding]),
    previewResponsePackage: vi.fn(async () => preview),
    getCommentLetterDraft: vi.fn(async () => draft),
    previewCommentLetter: vi.fn(async () => letterPreview),
    createResponsePackage: createPackageMock,
    addFindingsToPackage: addFindingsMock,
    issueResponsePackage: issueMock,
    createPackageRevision: revisionMock,
    generateCommentLetterDraft: generateLetterMock,
    updateCommentLetterDraft: updateLetterMock,
    updateResponsePackageItem: updateItemMock,
    markPackageReadyForHandoff: readyMock,
  };
});

import ResponsePackagesLandingPage from "@/app/projects/[projectId]/response-packages/page";
import ResponsePackageDetailPage from "@/app/projects/[projectId]/response-packages/[packageId]/page";
import ResponsePackagePreviewPage from "@/app/projects/[projectId]/response-packages/[packageId]/preview/page";
import CommentLetterDraftPage from "@/app/projects/[projectId]/comment-letter-drafts/[draftId]/page";
import CommentLetterPreviewPage from "@/app/projects/[projectId]/comment-letter-drafts/[draftId]/preview/page";
import ProjectDetailPage from "@/app/projects/[projectId]/page";
import CreateResponsePackageButton from "@/components/CreateResponsePackageButton";
import AddToResponsePackageButton from "@/components/AddToResponsePackageButton";
import ResponsePackageWorkflow from "@/components/ResponsePackageWorkflow";
import CommentLetterEditor from "@/components/CommentLetterEditor";

const projectId = "proj_1";

describe("Response packages landing page", () => {
  it("lists packages and links to each one", async () => {
    const { container } = render(
      await ResponsePackagesLandingPage({ params: { projectId } }),
    );
    expect(screen.getByText("Initial review comments")).toBeInTheDocument();
    const hrefs = Array.from(container.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    expect(hrefs).toContain(`/projects/${projectId}/response-packages/rpkg_1`);
  });
});

describe("Create response package button", () => {
  it("sends the title and type payload", async () => {
    render(<CreateResponsePackageButton projectId={projectId} />);
    fireEvent.change(screen.getByPlaceholderText("Initial review comments"), {
      target: { value: "Round 1 comments" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Create response package" }),
    );
    await waitFor(() => expect(createPackageMock).toHaveBeenCalled());
    expect(createPackageMock.mock.calls[0][1].packageTitle).toBe("Round 1 comments");
  });
});

describe("Response package detail page", () => {
  it("renders selected items and add panel", async () => {
    render(
      await ResponsePackageDetailPage({
        params: { projectId, packageId: "rpkg_1" },
      }),
    );
    expect(
      screen.getByText("Provide the detention outlet detail."),
    ).toBeInTheDocument();
    expect(screen.getByText("Add reviewer-selected records")).toBeInTheDocument();
  });
});

describe("Response package preview page", () => {
  it("renders the boundary statement and comment items", async () => {
    render(
      await ResponsePackagePreviewPage({
        params: { projectId, packageId: "rpkg_1" },
      }),
    );
    expect(screen.getByText(/does not approve plans/i)).toBeInTheDocument();
    expect(screen.getByText(/Comment 1/)).toBeInTheDocument();
  });
});

describe("Add to response package button", () => {
  it("adds a finding to the selected package", async () => {
    render(
      <AddToResponsePackageButton
        projectId={projectId}
        sourceType="finding"
        sourceId="find_1"
        packages={[pkg]}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Add to response package" }),
    );
    await waitFor(() => expect(addFindingsMock).toHaveBeenCalled());
    expect(addFindingsMock.mock.calls[0][2]).toEqual(["find_1"]);
  });

  it("prompts to create a package when none exist", () => {
    render(
      <AddToResponsePackageButton
        projectId={projectId}
        sourceType="finding"
        sourceId="find_1"
        packages={[]}
      />,
    );
    expect(
      screen.getByText(/No response package exists for this project yet/),
    ).toBeInTheDocument();
  });
});

describe("Response package workflow", () => {
  it("issues a package with a safe status flow", async () => {
    render(
      <ResponsePackageWorkflow projectId={projectId} packageId="rpkg_1" />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Issue package by reviewer" }),
    );
    await waitFor(() => expect(issueMock).toHaveBeenCalled());
    expect(issueMock.mock.calls[0][1]).toBe("rpkg_1");
  });

  it("creates a revision", async () => {
    render(
      <ResponsePackageWorkflow projectId={projectId} packageId="rpkg_1" />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Create revision" }));
    await waitFor(() => expect(revisionMock).toHaveBeenCalled());
  });
});

describe("Comment letter draft page and editor", () => {
  it("renders editable sections", async () => {
    render(
      await CommentLetterDraftPage({
        params: { projectId, draftId: "cldraft_1" },
      }),
    );
    expect(screen.getByText("Edit comment letter draft")).toBeInTheDocument();
    expect(screen.getByText(/does not approve plans/i)).toBeInTheDocument();
  });

  it("saves edits with a safe payload", async () => {
    render(<CommentLetterEditor projectId={projectId} draft={draft} />);
    fireEvent.click(screen.getByRole("button", { name: "Save edits" }));
    await waitFor(() => expect(updateLetterMock).toHaveBeenCalled());
    expect(updateLetterMock.mock.calls[0][1]).toBe("cldraft_1");
  });
});

describe("Comment letter preview page", () => {
  it("renders the boundary statement and sections", async () => {
    render(
      await CommentLetterPreviewPage({
        params: { projectId, draftId: "cldraft_1" },
      }),
    );
    expect(screen.getByText(/does not approve plans/i)).toBeInTheDocument();
    expect(screen.getByText("Review-support comments")).toBeInTheDocument();
  });
});

describe("Project overview Sprint 8 link", () => {
  it("links to response packages", async () => {
    const { container } = render(
      await ProjectDetailPage({ params: { projectId } }),
    );
    const hrefs = Array.from(container.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    expect(hrefs).toContain(`/projects/${projectId}/response-packages`);
  });
});

describe("Professional boundary in Sprint 8 UI", () => {
  it("uses no prohibited final-decision wording and leaks no secrets", async () => {
    const parts: string[] = [];
    parts.push(
      (
        render(await ResponsePackagesLandingPage({ params: { projectId } }))
          .container.textContent ?? ""
      ).toLowerCase(),
    );
    parts.push(
      (
        render(
          await ResponsePackageDetailPage({
            params: { projectId, packageId: "rpkg_1" },
          }),
        ).container.textContent ?? ""
      ).toLowerCase(),
    );
    parts.push(
      (
        render(
          await ResponsePackagePreviewPage({
            params: { projectId, packageId: "rpkg_1" },
          }),
        ).container.textContent ?? ""
      ).toLowerCase(),
    );
    parts.push(
      (
        render(
          await CommentLetterPreviewPage({
            params: { projectId, draftId: "cldraft_1" },
          }),
        ).container.textContent ?? ""
      ).toLowerCase(),
    );
    const text = parts.join(" ");
    // The boundary statement legitimately says "does not approve / resolve / close".
    // Strip the boundary sentences before scanning for prohibited final outcomes.
    const scrubbed = text
      .split(". ")
      .filter((s) => !s.includes("does not approve"))
      .join(". ");
    for (const word of PROHIBITED_WORDS) {
      expect(scrubbed).not.toContain(word);
    }
    for (const leak of FORBIDDEN_LEAKS) {
      expect(text).not.toContain(leak);
    }
  });
});
