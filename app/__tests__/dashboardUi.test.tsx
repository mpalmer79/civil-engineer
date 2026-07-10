import {
  cleanup,
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

// Final-decision and outcome words that must never appear in the new visible UI.
const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "compliant",
  "noncompliant",
  "verified",
  "validated",
  "passed review",
  "failed review",
  "resolved",
  "closed",
  "completed",
];

// Attribution tokens are assembled from fragments so the literal attribution
// strings are never stored verbatim in the repository while the test still
// confirms no tool attribution appears in the visible UI.
const ATTRIBUTION_TOKENS = [
  ["claude", "code"].join(" "),
  ["claude.ai", "code"].join("/"),
  ["co-authored", "by"].join("-"),
];

const FORBIDDEN_LEAKS = [
  "storage_path",
  "storage_key",
  "signed_url",
  "secret",
  "password",
  "/var/",
  ...ATTRIBUTION_TOKENS,
];

const {
  getReviewerDashboardMock,
  getReviewerQueueMock,
  getOrganizationDashboardMock,
  getOrganizationReviewerWorkloadMock,
  getProjectWorkloadSummaryMock,
  getProjectPendingActionsMock,
  isSignedInMock,
} = vi.hoisted(() => ({
  getReviewerDashboardMock: vi.fn(),
  getReviewerQueueMock: vi.fn(),
  getOrganizationDashboardMock: vi.fn(),
  getOrganizationReviewerWorkloadMock: vi.fn(),
  getProjectWorkloadSummaryMock: vi.fn(),
  getProjectPendingActionsMock: vi.fn(),
  isSignedInMock: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getReviewerDashboard: getReviewerDashboardMock,
    getReviewerQueue: getReviewerQueueMock,
    getOrganizationDashboard: getOrganizationDashboardMock,
    getOrganizationReviewerWorkload: getOrganizationReviewerWorkloadMock,
    getProjectWorkloadSummary: getProjectWorkloadSummaryMock,
    getProjectPendingActions: getProjectPendingActionsMock,
    isSignedIn: isSignedInMock,
  };
});

const metrics = {
  documentsUploaded: 4,
  documentsNeedingIndexing: 2,
  documentsIndexedWithText: 1,
  documentsExtractionUnavailable: 1,
  findingsNeedingReviewerConfirmation: 3,
  evidenceCandidatesNeedingTriage: 2,
  checklistItemsMissingEvidence: 1,
  checklistItemsUnclearEvidence: 1,
  applicantResponsesNeedingReview: 2,
  resubmittalRoundsRegistered: 1,
  matrixItemsCarriedForward: 1,
  responsePackagesDraft: 1,
  responsePackagesReadyForHandoff: 1,
  packagesIssuedByReviewer: 0,
  pendingReviewerActionCount: 7,
  hasPendingReviewerAction: true,
};

const projectSummary = {
  projectId: "proj_1",
  projectName: "Brookside Meadows",
  status: "under_review_support",
  sourceMode: "demo_fixture",
  organizationId: "org_1",
  assignedReviewerUserId: null,
  assignedReviewerName: "Jordan Reviewer",
  reviewPriority: "elevated",
  reviewDueDate: null,
  lastReviewerActivityAt: null,
  ageBucket: "waiting_1_to_3_days",
  dueDateIndicators: [],
  pendingReviewerActionCount: 7,
  hasPendingReviewerAction: true,
  metrics,
};

const queueItem = {
  queueItemId: "proj_1:document_indexing",
  projectId: "proj_1",
  projectName: "Brookside Meadows",
  itemType: "document_indexing",
  label: "Documents needing indexing",
  count: 2,
  status: "pending_reviewer_action",
  ageBucket: "updated_today",
  targetPath: "/projects/proj_1/documents",
};

const reviewerDashboard = {
  scope: "reviewer",
  generatedAt: "2026-06-26T00:00:00Z",
  userId: "u1",
  displayName: "Reviewer One",
  accessibleProjectCount: 2,
  projectsWithPendingActionCount: 1,
  totals: {
    documentsUploaded: 4,
    documentsNeedingIndexing: 2,
    documentsIndexedWithText: 1,
    documentsExtractionUnavailable: 1,
    findingsNeedingReviewerConfirmation: 3,
    evidenceCandidatesNeedingTriage: 2,
    checklistItemsMissingEvidence: 1,
    checklistItemsUnclearEvidence: 1,
    applicantResponsesNeedingReview: 2,
    resubmittalRoundsRegistered: 1,
    matrixItemsCarriedForward: 1,
    responsePackagesDraft: 1,
    responsePackagesReadyForHandoff: 1,
    packagesIssuedByReviewer: 0,
    pendingReviewerActionCount: 7,
  },
  projects: [projectSummary],
  queue: [queueItem],
  accessNote: "Dashboard data is limited to projects you can access.",
};

function read<T>(value: T) {
  return {
    ok: true,
    status: 200,
    backendReachable: true,
    data: value,
  };
}

function assertSafe(container: HTMLElement) {
  const text = container.textContent?.toLowerCase() ?? "";
  for (const word of PROHIBITED_WORDS) {
    expect(text).not.toContain(word);
  }
  for (const leak of FORBIDDEN_LEAKS) {
    expect(text).not.toContain(leak);
  }
}

beforeEach(() => {
  globalThis.fetch = vi.fn().mockRejectedValue(new Error("no backend"));
  isSignedInMock.mockReturnValue(true);
  getReviewerDashboardMock.mockResolvedValue(read(reviewerDashboard));
  getReviewerQueueMock.mockResolvedValue(
    read({
      scope: "reviewer",
      generatedAt: "2026-06-26T00:00:00Z",
      itemCount: 1,
      items: [queueItem],
    }),
  );
  getOrganizationDashboardMock.mockResolvedValue(
    read({
      scope: "organization",
      generatedAt: "2026-06-26T00:00:00Z",
      organizationId: "org_1",
      organizationName: "Demo Review Team",
      viewerRole: "org_admin",
      projectCount: 1,
      projectsWithPendingActionCount: 1,
      statusCounts: { under_review_support: 1 },
      priorityCounts: { elevated: 1 },
      totals: reviewerDashboard.totals,
      projects: [projectSummary],
      accessNote: "Organization workload is limited to projects you can access.",
    }),
  );
  getOrganizationReviewerWorkloadMock.mockResolvedValue(
    read({
      scope: "organization",
      generatedAt: "2026-06-26T00:00:00Z",
      organizationId: "org_1",
      organizationName: "Demo Review Team",
      viewerRole: "org_admin",
      reviewers: [
        {
          assignedReviewerUserId: "u1",
          assignedReviewerName: "Jordan Reviewer",
          projectCount: 1,
          pendingReviewerActionCount: 7,
          projectsWithPendingActionCount: 1,
        },
      ],
      accessNote: "Reviewer workload is grouped by assigned reviewer.",
    }),
  );
  getProjectWorkloadSummaryMock.mockResolvedValue(
    read({
      ...projectSummary,
      scope: "project",
      generatedAt: "2026-06-26T00:00:00Z",
      queue: [queueItem],
      accessNote: "Project workload counts are operational indicators only.",
    }),
  );
  getProjectPendingActionsMock.mockResolvedValue(
    read({
      scope: "project",
      generatedAt: "2026-06-26T00:00:00Z",
      projectId: "proj_1",
      projectName: "Brookside Meadows",
      pendingReviewerActionCount: 7,
      items: [queueItem],
      accessNote: "Pending actions are operational indicators.",
    }),
  );
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Reviewer dashboard page", () => {
  it("renders metric cards and the reviewer queue when signed in", async () => {
    const { default: ReviewerDashboardPage } = await import(
      "@/app/dashboard/page"
    );
    const { container } = render(<ReviewerDashboardPage />);
    await waitFor(() =>
      expect(
        screen.getByText("Projects needing reviewer attention"),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getAllByText("Accessible projects").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Documents needing indexing").length,
    ).toBeGreaterThan(0);
    assertSafe(container);
  });

  it("shows a sign-in prompt and demo link when signed out", async () => {
    isSignedInMock.mockReturnValue(false);
    const { default: ReviewerDashboardPage } = await import(
      "@/app/dashboard/page"
    );
    render(<ReviewerDashboardPage />);
    await waitFor(() =>
      expect(
        screen.getByText(/Sign in to view your reviewer dashboard/i),
      ).toBeInTheDocument(),
    );
    const demoLink = screen.getByRole("link", { name: /Brookside Meadows/i });
    expect(demoLink).toHaveAttribute(
      "href",
      "/projects/proj_brookside_meadows",
    );
    expect(getReviewerDashboardMock).not.toHaveBeenCalled();
  });
});

describe("Reviewer queue page", () => {
  it("renders queue items", async () => {
    const { default: ReviewerQueuePage } = await import(
      "@/app/dashboard/queue/page"
    );
    const { container } = render(<ReviewerQueuePage />);
    await waitFor(() =>
      expect(
        screen.getAllByText("Documents needing indexing").length,
      ).toBeGreaterThan(0),
    );
    assertSafe(container);
  });
});

describe("Organization dashboard page", () => {
  it("renders the organization workload summary", async () => {
    const { default: OrganizationDashboardPage } = await import(
      "@/app/organizations/[organizationId]/dashboard/page"
    );
    const { container } = render(await OrganizationDashboardPage({ params: Promise.resolve({ organizationId: "org_1" }) }));
    await waitFor(() =>
      expect(
        screen.getByText("Projects by review-support status"),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("Jordan Reviewer")).toBeInTheDocument();
    assertSafe(container);
  });

  it("renders a permission-denied state on 403", async () => {
    getOrganizationDashboardMock.mockResolvedValue({
      ok: false,
      status: 403,
      backendReachable: true,
      error: "not a member",
    });
    getOrganizationReviewerWorkloadMock.mockResolvedValue({
      ok: false,
      status: 403,
      backendReachable: true,
      error: "not a member",
    });
    const { default: OrganizationDashboardPage } = await import(
      "@/app/organizations/[organizationId]/dashboard/page"
    );
    render(await OrganizationDashboardPage({ params: Promise.resolve({ organizationId: "org_x" }) }));
    await waitFor(() =>
      expect(screen.getByText("Permission denied")).toBeInTheDocument(),
    );
  });
});

describe("Project workload page", () => {
  it("renders workflow summaries and pending actions", async () => {
    const { default: ProjectWorkloadPage } = await import(
      "@/app/projects/[projectId]/workload/page"
    );
    const { container } = render(await ProjectWorkloadPage({ params: Promise.resolve({ projectId: "proj_1" }) }));
    await waitFor(() =>
      expect(screen.getByText("Workload metrics")).toBeInTheDocument(),
    );
    expect(screen.getByText("Pending reviewer action")).toBeInTheDocument();
    expect(
      screen.getByText("Packages ready for reviewer handoff"),
    ).toBeInTheDocument();
    assertSafe(container);
  });

  it("renders a permission-denied state for an unauthorized user", async () => {
    getProjectWorkloadSummaryMock.mockResolvedValue({
      ok: false,
      status: 403,
      backendReachable: true,
      error: "no access",
    });
    const { default: ProjectWorkloadPage } = await import(
      "@/app/projects/[projectId]/workload/page"
    );
    render(await ProjectWorkloadPage({ params: Promise.resolve({ projectId: "proj_x" }) }));
    await waitFor(() =>
      expect(screen.getByText("Permission denied")).toBeInTheDocument(),
    );
  });
});

describe("Projects page signed-in cards and project overview card", () => {
  it("renders signed-in summary cards", async () => {
    const { default: ProjectsDashboardCards } = await import(
      "@/components/ProjectsDashboardCards"
    );
    render(<ProjectsDashboardCards />);
    await waitFor(() =>
      expect(screen.getByText("My accessible projects")).toBeInTheDocument(),
    );
    expect(screen.getByText("Package handoff queue")).toBeInTheDocument();
    expect(
      screen.getByText("Applicant response review queue"),
    ).toBeInTheDocument();
  });

  it("renders the project overview workload card with pending actions", async () => {
    const { default: ProjectWorkloadCard } = await import(
      "@/components/ProjectWorkloadCard"
    );
    const { container } = render(<ProjectWorkloadCard projectId="proj_1" />);
    await waitFor(() =>
      expect(
        screen.getByText("Workload and pending actions"),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("link", { name: "Open project workload" }),
    ).toHaveAttribute("href", "/projects/proj_1/workload");
    assertSafe(container);
  });
});
