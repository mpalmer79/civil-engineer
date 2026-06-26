import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { hotspots as staticHotspots } from "@/data/hotspots";

// Keep the homepage deterministic and offline: serve static hotspots instead of
// hitting the backend. projectMetrics and everything else stay real.
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getHotspots: vi.fn(async () => staticHotspots),
  };
});

import HomePage from "@/app/page";

// Cleanup is not globally configured, so reset the DOM between renders to avoid
// duplicate matches when the full page is rendered in more than one test.
afterEach(() => cleanup());

describe("HomePage illustrations", () => {
  it("renders an icon for each of the eight workflow steps", async () => {
    const ui = await HomePage();
    const { container } = render(ui);

    // Each workflow step title is present.
    expect(screen.getByText("Upload and parse DXF files")).toBeInTheDocument();
    expect(
      screen.getByText("View the reviewer command center"),
    ).toBeInTheDocument();

    // Each workflow step carries a small consistent icon (the h-5 line icons).
    const workflowIcons = container.querySelectorAll("svg.h-5.w-5");
    expect(workflowIcons.length).toBe(8);
  });

  it("renders the technical architecture diagram with accessible labels", async () => {
    const ui = await HomePage();
    render(ui);

    expect(screen.getByText("Next.js frontend")).toBeInTheDocument();
    expect(screen.getByText("FastAPI backend")).toBeInTheDocument();
    expect(screen.getByText("DXF parser")).toBeInTheDocument();
    expect(screen.getByText("Testing and coverage")).toBeInTheDocument();
  });

  it("keeps the backend status banner visible in the hero", async () => {
    const ui = await HomePage();
    render(ui);
    // The banner surfaces backend connection state and must not be hidden behind
    // imagery. Its initial "checking" message is unique to the banner.
    expect(
      screen.getByText(/Checking backend connection/i),
    ).toBeInTheDocument();
  });

  it("mentions the real-world foundation without overstating production readiness", async () => {
    const ui = await HomePage();
    render(ui);
    const heading = screen.getByText("Real-world foundation now in progress");
    // Scope assertions to the new section so the deliberate boundary-disclaimer
    // wording elsewhere on the page (the SafetyBoundaryBanner) is not matched.
    const section = heading.closest("section");
    const text = (section?.textContent ?? "").toLowerCase();
    // Future roadmap items are framed as future, not delivered.
    expect(text).toContain("future roadmap");
    // No final-decision or production-ready overstatement in the new section.
    for (const word of [
      "approved",
      "certified",
      "fully compliant",
      "production ready",
      "enterprise ready",
    ]) {
      expect(text).not.toContain(word);
    }
  });
});
