import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "@/app/page";
import { checklist } from "@/data/checklist";
import { documents } from "@/data/documents";
import { findings } from "@/data/findings";

const HERO_IMAGE_FILE = "site-plan-review-hero.webp";

const source = () =>
  readFileSync(join(process.cwd(), "app/page.tsx"), "utf8");

describe("HomePage hero", () => {
  it("leads with the product positioning headline", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /review stormwater submissions with evidence, context, and human control/i,
      }),
    ).toBeInTheDocument();
  });

  it("shows the site-plan review hero image with descriptive alt text", () => {
    const { container } = render(<HomePage />);
    const hero = screen.getByAltText(/preliminary site plan/i);
    expect(hero.getAttribute("src") ?? "").toContain(HERO_IMAGE_FILE);
    expect(container.querySelector(".aspect-\\[16\\/9\\]")).not.toBeNull();
  });

  it("references a hero image file that exists in public assets", () => {
    expect(
      existsSync(
        join(process.cwd(), "public/images/civil-engineer", HERO_IMAGE_FILE),
      ),
    ).toBe(true);
  });

  it("labels Brookside Meadows as a synthetic case study near the hero", () => {
    render(<HomePage />);
    expect(
      screen.getByText(/fictional 47-lot subdivision in the fictional town of hartwell/i),
    ).toBeInTheDocument();
    expect(screen.getAllByTestId("demo-data-badge").length).toBeGreaterThanOrEqual(1);
  });

  it("points the primary CTA at the guided demo and the secondary at the technical overview", () => {
    render(<HomePage />);
    const primary = screen.getByRole("link", {
      name: /start the brookside meadows guided demo/i,
    });
    expect(primary.getAttribute("href")).toBe("/guided-demo");
    const secondary = screen.getByRole("link", {
      name: /review the technical overview/i,
    });
    expect(secondary.getAttribute("href")).toBe("/start-here");
    expect(existsSync(join(process.cwd(), "app/guided-demo"))).toBe(true);
    expect(existsSync(join(process.cwd(), "app/start-here"))).toBe(true);
  });
});

describe("HomePage case-study facts", () => {
  it("derives counts from the seeded fixtures so copy cannot drift from data", () => {
    render(<HomePage />);
    expect(
      screen.getByText("Documents in the demo package").previousElementSibling
        ?.textContent,
    ).toBe(String(documents.length));
    expect(
      screen.getByText("Checklist items tracked").previousElementSibling
        ?.textContent,
    ).toBe(String(checklist.length));
    expect(
      screen.getByText("Review-support findings").previousElementSibling
        ?.textContent,
    ).toBe(String(findings.length));
  });

  it("labels the facts as fixed case-study facts, not live metrics", () => {
    render(<HomePage />);
    expect(
      screen.getByText(/fixed facts from the seeded review fixture, not live operational metrics/i),
    ).toBeInTheDocument();
  });
});

describe("HomePage reviewer workflow", () => {
  it("presents six stages that link into the Brookside project workspace", () => {
    render(<HomePage />);
    for (const stage of [
      /project intake/i,
      /document and dxf intake/i,
      /evidence indexing and retrieval/i,
      /checklist and finding review/i,
      /applicant response tracking/i,
      /reviewer-controlled handoff/i,
    ]) {
      expect(screen.getAllByText(stage).length).toBeGreaterThanOrEqual(1);
    }
    const stageLinks = screen
      .getAllByRole("link")
      .filter((a) =>
        (a.getAttribute("href") ?? "").startsWith("/projects/proj_brookside_meadows"),
      );
    expect(stageLinks.length).toBeGreaterThanOrEqual(6);
  });
});

describe("HomePage honesty guarantees", () => {
  it("renders no fabricated live-operations widgets", () => {
    const text = source();
    for (const forbidden of [
      "All Systems Operational",
      "Near You",
      "Recent Activity",
      "Priority Alerts",
      "2h ago",
    ]) {
      expect(text).not.toContain(forbidden);
    }
  });

  it("renders no operational sidebar competing with the global navigation", () => {
    const { container } = render(<HomePage />);
    expect(container.querySelector("aside")).toBeNull();
    expect(container.querySelector("nav")).toBeNull();
  });

  it("states the human review boundary", () => {
    render(<HomePage />);
    expect(
      screen.getByText(/ai provides review support\. you make the decisions\. every review is human\./i),
    ).toBeInTheDocument();
  });

  it("summarizes what is real versus seeded", () => {
    render(<HomePage />);
    expect(screen.getByText("Implemented")).toBeInTheDocument();
    expect(screen.getByText("Seeded demo")).toBeInTheDocument();
    expect(screen.getByText("Intentionally out of scope")).toBeInTheDocument();
  });

  it("documents both recruiter review paths", () => {
    render(<HomePage />);
    expect(screen.getByText(/five-minute product path/i)).toBeInTheDocument();
    expect(screen.getByText(/fifteen-minute technical path/i)).toBeInTheDocument();
  });
});

describe("HomePage semantic structure", () => {
  it("does not render its own main landmark because the root layout provides one", () => {
    const { container } = render(<HomePage />);
    expect(container.querySelector("main")).toBeNull();
  });

  it("labels every section with a heading", () => {
    const { container } = render(<HomePage />);
    const sections = Array.from(container.querySelectorAll("section"));
    expect(sections.length).toBeGreaterThanOrEqual(6);
    for (const section of sections) {
      expect(section.getAttribute("aria-labelledby")).toBeTruthy();
    }
  });
});

describe("HomePage language hygiene", () => {
  it("does not use prohibited final-decision wording as a product claim", () => {
    const text = source().toLowerCase();
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
      expect(text).not.toContain(phrase);
    }
  });

  it("does not include tool attribution in visible homepage copy", () => {
    const { container } = render(<HomePage />);
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).not.toContain(["claude", "code"].join(" "));
    expect(text).not.toContain(["claude.ai", "code"].join("/"));
    expect(text).not.toContain(["generated", "by"].join(" "));
    expect(text).not.toContain(["co-authored", "by"].join("-"));
  });

  it("does not use em dashes in homepage copy", () => {
    expect(source()).not.toContain("\u2014");
  });
});
