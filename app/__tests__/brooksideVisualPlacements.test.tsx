import { ok } from "@/lib/api/__tests__/testHelpers";
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { brooksideMedia } from "@/lib/brooksideMedia";
import { BROOKSIDE_PROJECT_ID } from "@/lib/demoJourney";

// Placement tests for the Brookside Meadows conceptual aerial: Start Here,
// Proof of Concept, Guided Demo, and the Projects workspace. The visual is
// reserved for the synthetic demo fixture; real project records never show
// Brookside imagery.

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("@/lib/analytics", () => ({
  trackDemoEvent: vi.fn(),
}));

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
    getProjectTraceability: vi.fn(async () =>
      ok({
        summary: {
          totalTraceabilityRows: 9,
          totalWorkflowItems: 6,
          totalPacketItems: 14,
          totalFindings: 7,
        },
      }),
    ),
    getPlanConsistencySummary: vi.fn(async () =>
      ok({ planConsistencyFindings: 4 }),
    ),
    getCadReviewFindings: vi.fn(async () => ok([{}, {}, {}])),
  };
});

import StartHerePage from "@/app/start-here/page";
import ProofOfConceptPage from "@/app/proof-of-concept/page";
import GuidedDemoPage from "@/app/guided-demo/page";
import ProjectsPage from "@/app/projects/page";

const baseProject = {
  projectId: BROOKSIDE_PROJECT_ID,
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

const realProject = {
  ...baseProject,
  projectId: "proj_user_abc123",
  projectName: "Maple Commons Stormwater Review",
  jurisdiction: "Town of Riverton",
  sourceMode: "user_created",
  documentCount: 1,
  findingCount: 0,
};

describe("Start Here Brookside section", () => {
  it("renders the aerial with the synthetic disclosure", () => {
    render(<StartHerePage />);
    expect(
      screen.getByRole("img", { name: brooksideMedia.image.alt }),
    ).toBeInTheDocument();
    expect(screen.getByText(brooksideMedia.disclosure)).toBeInTheDocument();
  });

  it("keeps the Start Guided Demo and Open Brookside Meadows actions", () => {
    render(<StartHerePage />);
    const section = screen
      .getByRole("heading", { name: "What is Brookside Meadows?" })
      .closest("section") as HTMLElement;
    const demoLink = within(section).getByRole("link", {
      name: "Start Guided Demo",
    });
    expect(demoLink).toHaveAttribute("href", "/guided-demo");
    const projectLink = within(section).getByRole("link", {
      name: "Open Brookside Meadows",
    });
    expect(projectLink).toHaveAttribute(
      "href",
      `/projects/${BROOKSIDE_PROJECT_ID}`,
    );
  });

  it("stacks the image above the text on mobile (image first in the DOM)", () => {
    render(<StartHerePage />);
    const heading = screen.getByRole("heading", {
      name: "What is Brookside Meadows?",
    });
    const section = heading.closest("section") as HTMLElement;
    const figure = within(section).getByTestId("brookside-project-visual");
    // A single-column grid renders in DOM order, so the figure preceding the
    // heading is what puts the image above the text on mobile.
    expect(
      figure.compareDocumentPosition(heading) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });
});

describe("Proof of Concept Brookside visual", () => {
  it("renders the aerial inside the What was tested section", () => {
    render(<ProofOfConceptPage />);
    const section = screen
      .getByRole("heading", { name: "What was tested" })
      .closest("section") as HTMLElement;
    expect(
      within(section).getByRole("img", { name: brooksideMedia.image.alt }),
    ).toBeInTheDocument();
  });

  it("distinguishes the visualization from the downloadable DXF", () => {
    render(<ProofOfConceptPage />);
    expect(screen.getByText(brooksideMedia.proofCaption)).toBeInTheDocument();
    // The caption never claims the image came from the DXF.
    expect(brooksideMedia.proofCaption).toContain("separately generated");
  });

  it("keeps the artifact downloads intact alongside the visual", () => {
    render(<ProofOfConceptPage />);
    expect(
      screen.getByRole("link", { name: "Download the test bundle" }),
    ).toBeInTheDocument();
  });
});

describe("Guided Demo Brookside cover", () => {
  it("renders the cover heading, supporting text, and disclosure", async () => {
    render(await GuidedDemoPage());
    expect(
      screen.getByRole("heading", { name: "Brookside Meadows Guided Review" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Follow a synthetic 47-lot subdivision through document intake, evidence review, findings, applicant responses, and reviewer-controlled handoff\./,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(brooksideMedia.disclosure)).toBeInTheDocument();
  });

  it("keeps the first demo action reachable below the cover", async () => {
    const { container } = render(await GuidedDemoPage());
    // The first tour step link still renders on load, so the cover did not
    // replace or bury the demo experience.
    expect(
      container.querySelector(
        `a[href="/projects/${BROOKSIDE_PROJECT_ID}/cad"]`,
      ),
    ).not.toBeNull();
  });
});

describe("Projects workspace Brookside imagery", () => {
  it("uses the aerial for the Brookside demo card only", async () => {
    listProjectsMock.mockResolvedValue(ok([baseProject, realProject]));
    render(await ProjectsPage());
    const visuals = screen.getAllByTestId("brookside-project-visual");
    expect(visuals).toHaveLength(1);
    expect(
      screen.getAllByRole("img", { name: brooksideMedia.image.alt }),
    ).toHaveLength(1);
    // The real project renders as a row without Brookside imagery.
    const realLink = screen.getByRole("link", {
      name: "Maple Commons Stormwater Review",
    });
    const row = realLink.closest("div") as HTMLElement;
    expect(within(row).queryByRole("img")).not.toBeInTheDocument();
  });

  it("shows no Brookside imagery when only real projects exist", async () => {
    listProjectsMock.mockResolvedValue(ok([realProject]));
    render(await ProjectsPage());
    expect(
      screen.queryByTestId("brookside-project-visual"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("img", { name: brooksideMedia.image.alt }),
    ).not.toBeInTheDocument();
  });
});
