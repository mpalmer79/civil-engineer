import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import HomePage from "@/app/page";
import { BROOKSIDE_PROJECT_ID } from "@/lib/demoJourney";
import { marketingMedia } from "@/lib/marketingMedia";

// Cleanup is not globally configured, so reset the DOM between renders to avoid
// duplicate matches when the full page is rendered in more than one test.
afterEach(() => cleanup());

const base = `/projects/${BROOKSIDE_PROJECT_ID}`;

describe("HomePage AEC pre-submittal QA positioning", () => {
  it("leads with an outcome-first headline aimed at civil/AEC firms", () => {
    render(HomePage());
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /catch stormwater review issues before submittal/i,
      }),
    ).toBeInTheDocument();
  });

  it("explains the pre-submittal QA outcome in the hero", () => {
    const { container } = render(HomePage());
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).toContain("pre-submittal qa");
    expect(text).toContain("review-support findings");
    expect(text).toContain("reduce avoidable resubmittal risk");
    expect(text).toContain("draft reviewer handoff package");
  });

  it("does not lead the hero with municipal reviewers as the buyer", () => {
    const { container } = render(HomePage());
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading.textContent?.toLowerCase()).not.toContain("municipal");
  });
});

describe("HomePage hero proof and capabilities", () => {
  it("highlights DXF/CAD intake, evidence traceability, and draft handoff", () => {
    const { container } = render(HomePage());
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).toContain("dxf");
    expect(text).toContain("traceability");
    expect(text).toContain("plan and report consistency");
    expect(text).toContain("draft reviewer handoff package");
  });

  it("links the four capabilities to real demo surfaces", () => {
    const { container } = render(HomePage());
    for (const href of [
      `${base}/cad`,
      `${base}/plan-consistency`,
      `${base}/traceability`,
      `${base}/review-packets`,
    ]) {
      expect(container.querySelector(`a[href="${href}"]`)).not.toBeNull();
    }
  });

  it("shows fixture-backed proof metrics from the seeded demo", () => {
    render(HomePage());
    expect(screen.getByText("Review-support findings")).toBeInTheDocument();
    expect(screen.getByText("Indexed documents")).toBeInTheDocument();
  });

  it("does not contain hero placeholder language", () => {
    const { container } = render(HomePage());
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).not.toContain("placeholder");
  });
});

describe("HomePage media-forward visuals", () => {
  it("renders marketing media images from the media manifests", () => {
    const { container } = render(HomePage());
    const images = container.querySelectorAll(
      'img[data-testid="marketing-media-image"]',
    );
    // Hero plus the four visual story sections plus the boundary visual.
    expect(images.length).toBeGreaterThanOrEqual(5);
    const srcs = Array.from(images).map((img) => img.getAttribute("src") ?? "");
    expect(
      srcs.every((src) => src.startsWith("/images/civil-engineer/")),
    ).toBe(true);
  });

  it("leads the hero with a real product image, not placeholder text", () => {
    const { container } = render(HomePage());
    const hero = container.querySelector(
      `img[src="${marketingMedia.hero.src}"]`,
    );
    expect(hero).not.toBeNull();
    expect(hero?.getAttribute("alt") ?? "").not.toBe("");
  });

  it("gives every marketing media image non-empty alt text", () => {
    const { container } = render(HomePage());
    const images = container.querySelectorAll(
      'img[data-testid="marketing-media-image"]',
    );
    for (const img of Array.from(images)) {
      expect((img.getAttribute("alt") ?? "").length).toBeGreaterThan(0);
    }
  });

  it("does not use hero visual placeholder language", () => {
    const { container } = render(HomePage());
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).not.toContain("hero visual placeholder");
    expect(text).not.toContain("placeholder");
  });
});

describe("HomePage primary demo call to action", () => {
  it("points the primary CTA at the guided demo route", () => {
    const { container } = render(HomePage());
    const primary = container.querySelector("a.btn.btn-primary");
    expect(primary).not.toBeNull();
    const href = primary?.getAttribute("href") ?? "";
    expect(href).toBe("/guided-demo");

    // The target maps to a real Next.js route directory, so the CTA cannot 404.
    const routeDir = join(process.cwd(), "app/guided-demo");
    expect(existsSync(routeDir)).toBe(true);
  });

  it("keeps the guided demo reachable as a secondary path", () => {
    const { container } = render(HomePage());
    expect(container.querySelector('a[href="/guided-demo"]')).not.toBeNull();
  });

  it("clearly labels the demo as a sample project with demo data", () => {
    const { container } = render(HomePage());
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).toContain("brookside meadows");
    expect(text).toContain("demo data");
    expect(text).toContain("sample project");
  });
});

describe("HomePage professional boundary", () => {
  it("keeps the professional boundary in a single section, not duplicated banners", () => {
    render(HomePage());
    // The full SafetyBoundaryBanner renders one "Professional boundary"
    // heading. Exactly one keeps the boundary as a single credibility section
    // rather than several top-level banners.
    expect(screen.getAllByText(/Professional boundary/i)).toHaveLength(1);
  });

  it("frames the boundary as human reviewers staying in control", () => {
    render(HomePage());
    expect(
      screen.getByRole("heading", { name: /human reviewers stay in control/i }),
    ).toBeInTheDocument();
  });

  it("keeps the backend status banner available", () => {
    render(HomePage());
    expect(screen.getByText(/Checking backend connection/i)).toBeInTheDocument();
  });
});

describe("HomePage pilot call to action", () => {
  it("links the pilot CTA to the public pilot request route", () => {
    const { container } = render(HomePage());
    const pilot = container.querySelector('a[href="/pilot"]');
    expect(pilot).not.toBeNull();
    expect(pilot?.textContent?.toLowerCase()).toContain("pilot");

    // The pilot CTA maps to a real Next.js route directory, so it cannot 404.
    expect(existsSync(join(process.cwd(), "app/pilot"))).toBe(true);
  });

  it("no longer shows a disabled pilot placeholder control", () => {
    render(HomePage());
    expect(
      screen.queryByRole("button", { name: /pilot access coming soon/i }),
    ).toBeNull();
  });
});

describe("HomePage language hygiene", () => {
  it("does not use prohibited final-decision wording as a product claim", () => {
    // Scan the homepage source rather than rendered output. The rendered page
    // includes the SafetyBoundaryBanner, which intentionally lists forbidden
    // vocabulary as examples of language the system never uses. Negative
    // boundary statements ("does not approve ... certify ... verify ...") live
    // in that banner, so source-scanning the page itself distinguishes a
    // product promise from a boundary disclaimer.
    const source = readFileSync(
      join(process.cwd(), "app/page.tsx"),
      "utf8",
    ).toLowerCase();
    for (const phrase of [
      "plan approved",
      "design validated",
      "fully compliant",
      "is certified",
      "are certified",
      "marked safe",
      "passed review",
      "pass review the first time",
      "guaranteed first-pass",
      "meets all requirements",
      "production ready",
    ]) {
      expect(source).not.toContain(phrase);
    }
  });

  it("does not include tool attribution in visible homepage copy", () => {
    const { container } = render(HomePage());
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).not.toContain("claude code");
    expect(text).not.toContain("claude.ai/code");
    expect(text).not.toContain("generated by");
    expect(text).not.toContain("co-authored-by");
  });

  it("does not contain stale sprint-number copy", () => {
    const { container } = render(HomePage());
    expect((container.textContent ?? "").toLowerCase()).not.toContain("sprint");
  });
});

describe("SaaS positioning document", () => {
  it("ships docs/SAAS_POSITIONING.md alongside the reframed homepage", () => {
    expect(existsSync(join(process.cwd(), "docs/SAAS_POSITIONING.md"))).toBe(
      true,
    );
  });
});
