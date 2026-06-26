import { readFileSync } from "node:fs";
import { join } from "node:path";

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

describe("HomePage positioning and discoverability", () => {
  it("positions the product as a stormwater review-support platform", async () => {
    const ui = await HomePage();
    const { container } = render(ui);
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).toContain("document-first");
    expect(text).toContain("evidence-first");
    expect(text).toContain("reviewer-controlled");
    expect(text).toContain("review-support platform");
    expect(text).toContain("municipal and civil engineering plan review");
  });

  it("renders hero CTAs for Projects and the Guided Demo", async () => {
    const ui = await HomePage();
    render(ui);
    expect(screen.getAllByText("Open Projects").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("See the Guided Demo").length,
    ).toBeGreaterThan(0);
    // The real workflow leads; CAD intake is a demo-specific action, not a
    // primary hero CTA.
    expect(screen.getAllByText(/Create a project record/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("View Rule Packs").length).toBeGreaterThan(0);
  });

  it("renders the Production foundation workflow section", async () => {
    const ui = await HomePage();
    render(ui);
    expect(
      screen.getByText("Production foundation workflow"),
    ).toBeInTheDocument();
    expect(screen.getByText("Create project record")).toBeInTheDocument();
    expect(screen.getByText("Index PDF pages")).toBeInTheDocument();
    expect(
      screen.getByText("Issue reviewer response package"),
    ).toBeInTheDocument();
  });

  it("renders the What is live now section as scannable groups", async () => {
    const ui = await HomePage();
    render(ui);
    expect(screen.getByText("What is live now")).toBeInTheDocument();
    expect(
      screen.getByText("Project records and access"),
    ).toBeInTheDocument();
    expect(screen.getByText("Documents and evidence")).toBeInTheDocument();
    expect(screen.getByText("Review workflow")).toBeInTheDocument();
    expect(screen.getByText("Reviewer communication")).toBeInTheDocument();
    // Brookside Meadows is labeled separately as the public demo fixture.
    expect(
      screen.getByText(/public guided demo fixture/i),
    ).toBeInTheDocument();
  });

  it("renders the Public demo vs real project workflow section", async () => {
    const ui = await HomePage();
    render(ui);
    expect(
      screen.getByText("Public demo vs real project workflow"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Public demo").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Real project workflow").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Sign in required/i)).toBeInTheDocument();
    expect(screen.getByText(/No account required/i)).toBeInTheDocument();
  });

  it("keeps the backend status banner visible in the hero", async () => {
    const ui = await HomePage();
    render(ui);
    expect(
      screen.getByText(/Checking backend connection/i),
    ).toBeInTheDocument();
  });

  it("keeps the professional boundary banner visible", async () => {
    const ui = await HomePage();
    render(ui);
    expect(
      screen.getAllByText(/Professional boundary/i).length,
    ).toBeGreaterThan(0);
  });

  it("does not contain stale build-status claims", async () => {
    const ui = await HomePage();
    const { container } = render(ui);
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).not.toContain("not part of the current build");
    expect(text).not.toContain("authentication is not part");
    expect(text).not.toContain("retrieval is not part");
  });

  it("does not include Sprint 9 dashboard language because those routes do not exist yet", async () => {
    const ui = await HomePage();
    const { container } = render(ui);
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).not.toContain("reviewer dashboard");
    expect(text).not.toContain("reviewer queue");
  });

  it("does not use prohibited final-decision wording as a claim in the homepage source", () => {
    // Scan the homepage source rather than rendered output. The rendered page
    // includes the SafetyBoundaryBanner, which intentionally displays forbidden
    // vocabulary (fully compliant, certified, and so on) as examples of language
    // the system never uses. Affirmative claims would only originate in the page
    // copy itself, so the source is the right surface to assert against.
    const source = readFileSync(
      join(process.cwd(), "app/page.tsx"),
      "utf8",
    ).toLowerCase();
    // Affirmative outcome wording, distinct from negated boundary disclaimers
    // such as "does not approve" or "no final approval workflow".
    for (const phrase of [
      "plan approved",
      "design validated",
      "fully compliant",
      "is certified",
      "are certified",
      "marked safe",
      "passed review",
      "production ready",
      "enterprise ready",
    ]) {
      expect(source).not.toContain(phrase);
    }
  });

  it("does not include tool attribution in visible homepage copy", async () => {
    const ui = await HomePage();
    const { container } = render(ui);
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).not.toContain("claude code");
    expect(text).not.toContain("claude.ai/code");
    expect(text).not.toContain("generated by");
    expect(text).not.toContain("co-authored-by");
  });
});
