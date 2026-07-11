import { ok } from "@/lib/api/__tests__/testHelpers";
import { existsSync } from "node:fs";
import { join } from "node:path";

import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BROOKSIDE_PROJECT_ID } from "@/lib/demoJourney";

const base = `/projects/${BROOKSIDE_PROJECT_ID}`;

// Affirmative final-decision wording that must never appear as a product promise,
// badge, CTA, or conclusion. Negative boundary statements ("does not approve ...
// certify ... verify ... validate") are allowed and are checked separately.
const PROHIBITED_PROMISES = [
  "plan approved",
  "plans approved",
  "design validated",
  "passes review",
  "passed review",
  "guaranteed compliance",
  "fully compliant",
  "first-pass acceptance",
  "meets all requirements",
];

// Mock the analytics helper so we can assert the demo instruments its events.
const trackDemoEvent = vi.fn();
vi.mock("@/lib/analytics", () => ({
  trackDemoEvent: (...args: unknown[]) => trackDemoEvent(...args),
}));

// Mock the demo count sources so the proof band is fixture-backed and
// deterministic. Counts mirror the shape the real API client returns.
const getProjectTraceability = vi.fn();
const getPlanConsistencySummary = vi.fn();
const getCadReviewFindings = vi.fn();

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getProjectTraceability: (...a: unknown[]) => getProjectTraceability(...a),
    getPlanConsistencySummary: (...a: unknown[]) =>
      getPlanConsistencySummary(...a),
    getCadReviewFindings: (...a: unknown[]) => getCadReviewFindings(...a),
  };
});

import GuidedDemoPage from "@/app/guided-demo/page";

function withCounts() {
  getProjectTraceability.mockResolvedValue(
    ok({
      summary: {
        totalTraceabilityRows: 9,
        totalWorkflowItems: 6,
        totalPacketItems: 14,
        totalFindings: 7,
      },
    }),
  );
  getPlanConsistencySummary.mockResolvedValue(ok({ planConsistencyFindings: 4 }));
  getCadReviewFindings.mockResolvedValue(ok([{}, {}, {}]));
}

beforeEach(() => {
  trackDemoEvent.mockReset();
  getProjectTraceability.mockReset();
  getPlanConsistencySummary.mockReset();
  getCadReviewFindings.mockReset();
  withCounts();
});

afterEach(() => cleanup());

describe("Guided demo route", () => {
  it("renders the guided demo as a sample project with demo data", async () => {
    render(await GuidedDemoPage());
    expect(
      screen.getByRole("heading", {
        name: /run the brookside meadows pre-submittal qa/i,
      }),
    ).toBeInTheDocument();
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).toContain("sample project");
    expect(text).toContain("demo data");
    expect(text).toContain("brookside meadows");
  });

  it("walks the five AEC pre-submittal QA steps", async () => {
    render(await GuidedDemoPage());
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).toContain("cad / dxf intake");
    expect(text).toContain("plan and report consistency");
    expect(text).toContain("evidence traceability");
    expect(text).toContain("workflow board");
    expect(text).toContain("draft reviewer handoff");
  });

  it("links each step to a real, non-404 Brookside Meadows route", async () => {
    const { container } = render(await GuidedDemoPage());
    // The tour shows one step at a time, so the first step's link and the
    // next-step CTAs are present in the DOM on load.
    expect(container.querySelector(`a[href="${base}/cad"]`)).not.toBeNull();
    expect(
      container.querySelector(`a[href="${base}/command-center"]`),
    ).not.toBeNull();
    expect(container.querySelector(`a[href="${base}"]`)).not.toBeNull();
    // Every step target maps to a real Next.js route directory, so no step can
    // 404, including the steps reached by navigating the tour.
    for (const dir of [
      "app/projects/[projectId]/cad",
      "app/projects/[projectId]/plan-consistency",
      "app/projects/[projectId]/traceability",
      "app/projects/[projectId]/workflow-board",
      "app/projects/[projectId]/review-packets",
      "app/projects/[projectId]/command-center",
    ]) {
      expect(existsSync(join(process.cwd(), dir))).toBe(true);
    }
  });

  it("points the final pilot CTA at the public pilot route", async () => {
    const { container } = render(await GuidedDemoPage());
    const pilot = container.querySelector('a[href="/pilot"]');
    expect(pilot).not.toBeNull();
    expect(pilot?.textContent?.toLowerCase()).toContain("pilot");
    expect(existsSync(join(process.cwd(), "app/pilot"))).toBe(true);
  });

  it("shows fixture-backed proof counts when available", async () => {
    render(await GuidedDemoPage());
    expect(screen.getByText("Traceability rows")).toBeInTheDocument();
    expect(screen.getByText("9")).toBeInTheDocument();
    expect(screen.getByText("CAD review-support findings")).toBeInTheDocument();
    expect(screen.getByText("Plan consistency findings")).toBeInTheDocument();
  });

  it("falls back to qualitative proof when counts are unavailable", async () => {
    const unavailable = {
      ok: false as const,
      kind: "network" as const,
      message: "Backend unavailable.",
      retryable: true,
    };
    getProjectTraceability.mockResolvedValue(unavailable);
    getPlanConsistencySummary.mockResolvedValue(unavailable);
    getCadReviewFindings.mockResolvedValue(unavailable);
    render(await GuidedDemoPage());
    // The labels still render; the values degrade to a qualitative marker.
    expect(screen.getByText("Traceability rows")).toBeInTheDocument();
    expect(screen.getAllByText("Included").length).toBeGreaterThan(0);
  });

  it("instruments demo analytics events", async () => {
    render(await GuidedDemoPage());
    const events = trackDemoEvent.mock.calls.map((c) => c[0]);
    expect(events).toContain("demo_started");
    expect(events).toContain("demo_step_viewed");
  });

  it("does not make fake timing claims", async () => {
    render(await GuidedDemoPage());
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).not.toMatch(/\d+\s*seconds?/);
    expect(text).not.toContain("in seconds");
  });

  it("does not use placeholder hero language", async () => {
    render(await GuidedDemoPage());
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).not.toContain("placeholder");
  });

  it("keeps boundary language present but below the demo story", async () => {
    render(await GuidedDemoPage());
    const text = document.body.textContent ?? "";
    expect(text).toContain("Human reviewers stay responsible");
    // The product story leads; the boundary reassurance comes after it.
    const storyIndex = text.indexOf("Run the Brookside Meadows pre-submittal QA");
    const boundaryIndex = text.indexOf("Human reviewers stay responsible");
    expect(storyIndex).toBeGreaterThanOrEqual(0);
    expect(boundaryIndex).toBeGreaterThan(storyIndex);
  });

  it("does not use prohibited final-decision wording as a product promise", async () => {
    render(await GuidedDemoPage());
    const text = (document.body.textContent ?? "").toLowerCase();
    for (const phrase of PROHIBITED_PROMISES) {
      expect(text).not.toContain(phrase);
    }
  });

  it("allows negative boundary statements about what it does not do", async () => {
    render(await GuidedDemoPage());
    const boundary = screen
      .getByText("Human reviewers stay responsible")
      .closest("section");
    expect(boundary).not.toBeNull();
    expect(
      within(boundary as HTMLElement).getByText(
        /does not approve, certify, verify, validate/i,
      ),
    ).toBeInTheDocument();
  });
});
