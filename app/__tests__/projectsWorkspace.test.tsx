import { ok } from "@/lib/api/__tests__/testHelpers";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

// SignInNotice and ProjectsDashboardCards are client components that read auth
// state; keep them offline and signed out so the projects workspace renders its
// public layout deterministically.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

// Final-decision wording the projects workspace must never present as a status.
const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "compliant",
  "verified",
  "validated",
  "passed review",
  "failed review",
  "resolved",
];

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
  assignedReviewerUserId: null,
  assignedReviewerName: null,
  reviewPriority: null,
  reviewDueDate: null,
  lastReviewerActivityAt: null,
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
  documentCount: 1,
  findingCount: 0,
  auditEventCount: 2,
};

const { listProjectsMock } = vi.hoisted(() => ({
  listProjectsMock: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    listProjects: listProjectsMock,
    isSignedIn: vi.fn(() => false),
    getReviewerDashboard: vi.fn(async () => ({
      ok: false,
      status: 200,
      backendReachable: true,
      data: null,
    })),
  };
});

import ProjectsPage from "@/app/projects/page";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Projects workspace", () => {
  it("renders a workspace header with a create project record action", async () => {
    listProjectsMock.mockResolvedValue(ok([demoProject, userProject]));
    render(await ProjectsPage());
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(
      screen.getAllByText("Create project record").length,
    ).toBeGreaterThan(0);
  });

  it("separates the public demo from real project records", async () => {
    listProjectsMock.mockResolvedValue(ok([demoProject, userProject]));
    render(await ProjectsPage());
    expect(screen.getByText("Real project records")).toBeInTheDocument();
    expect(screen.getByText("Public guided demo")).toBeInTheDocument();
    // Each project name renders exactly once (single responsive DOM row).
    expect(
      screen.getByText("Maple Commons Stormwater Review"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Brookside Meadows Residential Subdivision"),
    ).toBeInTheDocument();
    expect(screen.getByText("Demo fixture")).toBeInTheDocument();
    expect(screen.getByText("User-created")).toBeInTheDocument();
  });

  it("shows a polished empty state when no real project records exist", async () => {
    listProjectsMock.mockResolvedValue(ok([demoProject]));
    render(await ProjectsPage());
    expect(
      screen.getByText("No real project records yet"),
    ).toBeInTheDocument();
    // The public demo still renders below the empty state.
    expect(screen.getByText("Public guided demo")).toBeInTheDocument();
  });

  it("surfaces a backend alert without hiding the error", async () => {
    listProjectsMock.mockResolvedValue({ ok: false, kind: "network", message: "Backend unavailable.", retryable: true });
    render(await ProjectsPage());
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Backend required");
  });

  it("uses no prohibited final-decision wording", async () => {
    listProjectsMock.mockResolvedValue(ok([demoProject, userProject]));
    const { container } = render(await ProjectsPage());
    const text = (container.textContent ?? "").toLowerCase();
    for (const word of PROHIBITED_WORDS) {
      expect(text).not.toContain(word);
    }
  });
});
