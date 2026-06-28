import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import StartHerePage from "@/app/start-here/page";
import GuidedDemoCard from "@/components/GuidedDemoCard";
import {
  BROOKSIDE_PROJECT_ID,
  demoJourneySteps,
  technicalFoundation,
} from "@/lib/demoJourney";

afterEach(() => cleanup());

// Affirmative final-decision wording that must never appear in the demo-facing
// UI. Negated boundary wording ("does not approve plans") and the safety
// banner's list of never-used words are allowed, so check for outcome phrases
// rather than bare words.
const PROHIBITED_WORDS = [
  "plan approved",
  "plans approved",
  "design validated",
  "passed review",
  "failed review",
  "issue resolved",
  "issue closed",
];

// Attribution tokens assembled from fragments so the literal strings are never
// stored verbatim while still asserting their absence in the visible UI.
const ATTRIBUTION_TOKENS = [
  ["claude", "code"].join(" "),
  ["claude.ai", "code"].join("/"),
  ["co-authored", "by"].join("-"),
  ["generated", "by"].join(" "),
];

function assertSafe(container: HTMLElement) {
  const text = (container.textContent ?? "").toLowerCase();
  for (const word of PROHIBITED_WORDS) {
    expect(text).not.toContain(word);
  }
  for (const token of ATTRIBUTION_TOKENS) {
    expect(text).not.toContain(token);
  }
  // No raw secrets or storage internals in the demo UI.
  for (const leak of ["storage_key", "signed_url", "bearer ey", "/home/"]) {
    expect(text).not.toContain(leak);
  }
}

describe("Demo journey data", () => {
  it("defines a twelve-step reviewer journey in order", () => {
    expect(demoJourneySteps).toHaveLength(12);
    expect(demoJourneySteps.map((s) => s.step)).toEqual([
      1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
    ]);
  });

  it("routes most steps through the Brookside Meadows sample project", () => {
    const base = `/projects/${BROOKSIDE_PROJECT_ID}`;
    const brooksideSteps = demoJourneySteps.filter((s) =>
      s.href.startsWith(base),
    );
    expect(brooksideSteps.length).toBeGreaterThanOrEqual(10);
    // The journey ends at the operational dashboard.
    expect(demoJourneySteps[11].href).toBe("/dashboard");
  });
});

describe("GuidedDemoCard", () => {
  it("renders the step number, title, what-to-notice, and link", () => {
    render(<GuidedDemoCard step={demoJourneySteps[0]} />);
    expect(screen.getByText("Review the sample project")).toBeInTheDocument();
    expect(screen.getByText(/What to notice:/)).toBeInTheDocument();
    const link = screen.getByTestId("demo-step-card");
    expect(link).toHaveAttribute(
      "href",
      `/projects/${BROOKSIDE_PROJECT_ID}`,
    );
  });
});

describe("Start Here page", () => {
  it("renders the Start Here hero and primary guided-demo CTA", () => {
    const { container } = render(<StartHerePage />);
    expect(
      screen.getByRole("heading", { name: "Start the Brookside Meadows demo" }),
    ).toBeInTheDocument();
    const startGuided = screen.getAllByRole("link", {
      name: "Start Guided Demo",
    });
    expect(startGuided.length).toBeGreaterThan(0);
    expect(startGuided[0]).toHaveAttribute("href", "/guided-demo");
    assertSafe(container);
  });

  it("describes Brookside Meadows as a synthetic public demo fixture", () => {
    render(<StartHerePage />);
    expect(
      screen.getByRole("heading", { name: "What is Brookside Meadows?" }),
    ).toBeInTheDocument();
    const text = document.body.textContent?.toLowerCase() ?? "";
    expect(text).toContain("synthetic public demo fixture");
  });

  it("offers an Open Brookside Meadows CTA", () => {
    render(<StartHerePage />);
    const openBrookside = screen.getAllByRole("link", {
      name: "Open Brookside Meadows",
    });
    expect(openBrookside.length).toBeGreaterThan(0);
    expect(openBrookside[0]).toHaveAttribute(
      "href",
      `/projects/${BROOKSIDE_PROJECT_ID}`,
    );
  });

  it("renders the technical foundation section", () => {
    render(<StartHerePage />);
    expect(screen.getByText("Technical foundation")).toBeInTheDocument();
    expect(screen.getByText(technicalFoundation[0].title)).toBeInTheDocument();
    expect(screen.getByText("FastAPI backend")).toBeInTheDocument();
  });

  it("renders all twelve demo step cards", () => {
    render(<StartHerePage />);
    expect(screen.getAllByTestId("demo-step-card")).toHaveLength(12);
  });
});
