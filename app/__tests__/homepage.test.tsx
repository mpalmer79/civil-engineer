import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import HomeDashboard from "@/app/page";

// Cleanup is not globally configured, so reset the DOM between renders to avoid
// duplicate matches when the full page is rendered in more than one test.
afterEach(() => cleanup());

const HERO_IMAGE_FILE = "brookside-project-thumbnail.webp";
const HERO_IMAGE_ALT = "Brookside Meadows residential subdivision aerial view";

describe("HomeDashboard recruiter-facing hero", () => {
  it("leads with the Reviewer Command Center heading and positioning line", () => {
    render(<HomeDashboard />);
    expect(
      screen.getByRole("heading", { level: 1, name: /reviewer command center/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/document-first\. evidence-first\. reviewer-controlled\./i),
    ).toBeInTheDocument();
  });

  it("shows the Brookside Meadows hero image with descriptive alt text", () => {
    const { container } = render(<HomeDashboard />);
    const hero = screen.getByAltText(HERO_IMAGE_ALT);
    expect(hero).toBeInTheDocument();
    expect(hero.getAttribute("src") ?? "").toContain(HERO_IMAGE_FILE);
    // The hero card keeps a stable aspect ratio and cover fit.
    expect(container.querySelector(".aspect-\\[16\\/9\\]")).not.toBeNull();
  });

  it("references a hero image file that exists in public assets", () => {
    const imagePath = join(
      process.cwd(),
      "public/images/civil-engineer",
      HERO_IMAGE_FILE,
    );
    expect(existsSync(imagePath)).toBe(true);
  });

  it("explains the Brookside Meadows demo project near the hero", () => {
    render(<HomeDashboard />);
    expect(
      screen.getByText(/synthetic 47-lot residential subdivision/i),
    ).toBeInTheDocument();
  });

  it("does not overlay duplicate Brookside Meadows text on the hero image card", () => {
    // The description lives outside the image container. The image card only
    // contains the Image element, so no text is layered over the visual.
    const { container } = render(<HomeDashboard />);
    const heroCard = container.querySelector(".aspect-\\[16\\/9\\]");
    expect(heroCard?.textContent ?? "").toBe("");
  });
});

describe("HomeDashboard proof chips", () => {
  const chips = [
    "Stormwater review workflow",
    "PDF evidence citations",
    "DXF and plan review support",
    "Applicant response tracking",
    "Human reviewer handoff",
  ];

  it("lists compact proof chips before the KPI cards", () => {
    render(<HomeDashboard />);
    for (const chip of chips) {
      expect(screen.getByText(chip)).toBeInTheDocument();
    }
  });
});

describe("HomeDashboard call-to-action links", () => {
  const ctas = [
    { name: /start guided demo/i, href: "/guided-demo", routeDir: "app/guided-demo" },
    { name: /open review queue/i, href: "/dashboard/queue", routeDir: "app/dashboard/queue" },
    { name: /view projects/i, href: "/projects", routeDir: "app/projects" },
  ];

  it("points each CTA at a real Next.js route", () => {
    render(<HomeDashboard />);
    for (const cta of ctas) {
      const link = screen.getByRole("link", { name: cta.name });
      expect(link.getAttribute("href")).toBe(cta.href);
      expect(existsSync(join(process.cwd(), cta.routeDir))).toBe(true);
    }
  });
});

describe("HomeDashboard operational dashboard", () => {
  it("keeps the KPI cards with their values and links", () => {
    const { container } = render(<HomeDashboard />);
    for (const kpi of [
      { label: "Projects", value: "24" },
      { label: "In Review", value: "18" },
      { label: "Pending Response", value: "7" },
      { label: "Ready for Handoff", value: "5" },
    ]) {
      const card = Array.from(container.querySelectorAll("a")).find(
        (a) => a.textContent?.includes(kpi.label) && a.textContent?.includes(kpi.value),
      );
      expect(card, `KPI card for ${kpi.label}`).toBeTruthy();
    }
  });

  it("keeps the dashboard widgets", () => {
    render(<HomeDashboard />);
    for (const heading of [
      "Active Workload",
      "Recent Activity",
      "Priority Alerts",
      "Map Overview",
      "System Guidance",
    ]) {
      expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
    }
  });

  it("does not repeat the hero image inside the Map Overview widget", () => {
    render(<HomeDashboard />);
    const heroImages = screen
      .getAllByRole("img")
      .filter((img) => (img.getAttribute("src") ?? "").includes(HERO_IMAGE_FILE));
    expect(heroImages).toHaveLength(1);
  });
});

describe("HomeDashboard human review boundary", () => {
  it("states that every review is human", () => {
    render(<HomeDashboard />);
    const statements = screen.getAllByText(
      /ai provides review support\. you make the decisions\. every review is human\./i,
    );
    expect(statements.length).toBeGreaterThanOrEqual(1);
  });

  it("offers a compact reviewer inspection path near the CTAs", () => {
    render(<HomeDashboard />);
    expect(
      screen.getByText(/review path: start with the guided demo/i),
    ).toBeInTheDocument();
  });
});

describe("HomeDashboard semantic structure", () => {
  it("does not render its own main landmark because the root layout provides one", () => {
    const { container } = render(<HomeDashboard />);
    expect(container.querySelector("main")).toBeNull();
  });

  it("labels the hero, proof, and dashboard sections", () => {
    const { container } = render(<HomeDashboard />);
    expect(container.querySelectorAll("section").length).toBeGreaterThanOrEqual(3);
  });
});

describe("HomeDashboard language hygiene", () => {
  const source = () =>
    readFileSync(join(process.cwd(), "app/page.tsx"), "utf8").toLowerCase();

  it("does not use prohibited final-decision wording as a product claim", () => {
    for (const phrase of [
      "plan approved",
      "design validated",
      "fully compliant",
      "is certified",
      "are certified",
      "marked safe",
      "passed review",
      "production ready",
    ]) {
      expect(source()).not.toContain(phrase);
    }
  });

  it("does not include tool attribution in visible homepage copy", () => {
    const { container } = render(<HomeDashboard />);
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).not.toContain("claude code");
    expect(text).not.toContain("claude.ai/code");
    expect(text).not.toContain("generated by");
    expect(text).not.toContain("co-authored-by");
  });

  it("does not use em dashes in homepage copy", () => {
    expect(source()).not.toContain("—");
  });
});
