import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import StartHerePage from "@/app/start-here/page";
import {
  BROOKSIDE_PROJECT_ID,
  demoJourneySteps,
  fiveMinutePath,
  technicalPath,
  outOfScope,
  reviewerChecklist,
} from "@/lib/demoJourney";

afterEach(() => cleanup());

const root = process.cwd();
function readDoc(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

describe("Demo journey link validation", () => {
  it("gives every demo step a valid absolute href", () => {
    for (const step of demoJourneySteps) {
      expect(step.href.startsWith("/")).toBe(true);
      expect(step.href).not.toContain("undefined");
    }
  });

  it("scopes Brookside steps to the seeded project id", () => {
    const base = `/projects/${BROOKSIDE_PROJECT_ID}`;
    const scoped = demoJourneySteps.filter((s) => s.href.startsWith(base));
    expect(scoped.length).toBeGreaterThanOrEqual(10);
  });

  it("gives every five-minute path entry a valid href", () => {
    expect(fiveMinutePath.length).toBe(6);
    for (const item of fiveMinutePath) {
      expect(item.href.startsWith("/")).toBe(true);
      expect(item.href).not.toContain("undefined");
    }
    // The fast path starts at Start Here and ends at deployment status.
    expect(fiveMinutePath[0].href).toBe("/start-here");
    expect(fiveMinutePath[fiveMinutePath.length - 1].href).toBe(
      "/deployment-status",
    );
  });
});

describe("Start Here evaluation pathways", () => {
  it("renders the evaluation pathways section", () => {
    render(<StartHerePage />);
    expect(screen.getByText("Evaluate the platform")).toBeInTheDocument();
    expect(screen.getByText("Evaluation pathways")).toBeInTheDocument();
    expect(screen.getByText("Product evaluation path")).toBeInTheDocument();
    expect(screen.getByText("Technical evaluation path")).toBeInTheDocument();
  });

  it("renders what to notice and intentionally out of scope", () => {
    render(<StartHerePage />);
    expect(screen.getByText("What to notice")).toBeInTheDocument();
    expect(
      screen.getByText("Intentionally out of scope"),
    ).toBeInTheDocument();
    expect(screen.getByText(outOfScope[0])).toBeInTheDocument();
    expect(screen.getByText(technicalPath[0])).toBeInTheDocument();
  });

  it("renders the reviewer walkthrough checklist", () => {
    render(<StartHerePage />);
    expect(
      screen.getByText("Reviewer walkthrough checklist"),
    ).toBeInTheDocument();
    // "Open Brookside Meadows" also appears as a CTA, so it can repeat.
    expect(screen.getAllByText(reviewerChecklist[0]).length).toBeGreaterThan(0);
    expect(screen.getByText("Inspect indexed pages")).toBeInTheDocument();
    expect(
      screen.getByText(reviewerChecklist[reviewerChecklist.length - 1]),
    ).toBeInTheDocument();
  });

  it("keeps a deployment status entry point on the fast path", () => {
    render(<StartHerePage />);
    const deploymentLinks = screen
      .getAllByRole("link")
      .filter((a) => a.getAttribute("href") === "/deployment-status");
    expect(deploymentLinks.length).toBeGreaterThan(0);
  });
});

describe("README portfolio presentation", () => {
  const readme = readDoc("README.md");

  it("includes the live demo URL and key demo routes", () => {
    expect(readme).toContain("https://civil-engineer.up.railway.app/");
    expect(readme).toContain("/start-here");
    expect(readme).toContain("/guided-demo");
  });

  it("presents the product overview, capabilities, and documentation map", () => {
    expect(readme).toContain("Product overview");
    expect(readme).toContain("Core platform capabilities");
    expect(readme).toContain("## Documentation");
  });

  it("keeps the review-support boundary and avoids overclaims", () => {
    const lower = readme.toLowerCase();
    expect(lower).toContain("does not");
    expect(lower).toContain("review-support");
    // No enterprise-readiness or certification overclaims.
    expect(lower).not.toContain("soc 2");
    expect(lower).not.toContain("fully compliant");
  });
});

describe("Live site verification doc", () => {
  const doc = readDoc("docs/OPERATIONS.md");

  it("includes Start Here and guided demo checks", () => {
    expect(doc).toContain("/start-here");
    expect(doc).toContain("/guided-demo");
  });

  it("includes a mobile nav auto-collapse check", () => {
    expect(doc.toLowerCase()).toContain("auto-collapse");
  });

  it("includes backend health and readiness checks", () => {
    expect(doc).toContain("/health");
    expect(doc).toContain("/api/v1/readiness");
  });
});
