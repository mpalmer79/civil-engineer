import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import HomePage from "@/app/page";
import { marketingMedia } from "@/lib/marketingMedia";

// Cleanup is not globally configured, so reset the DOM between renders to avoid
// duplicate matches when the full page is rendered in more than one test.
afterEach(() => cleanup());

function imageBySrc(container: HTMLElement, src: string) {
  return container.querySelector(`img[src="${src}"]`);
}

describe("HomePage media-first layout", () => {
  it("positions the product as a stormwater review-support platform", () => {
    const { container } = render(HomePage());
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).toContain("document-first");
    expect(text).toContain("evidence-first");
    expect(text).toContain("reviewer-controlled");
    expect(text).toContain("review-support platform");
    expect(text).toContain("municipal and civil engineering plan review");
  });

  it("renders the hero media placeholder", () => {
    const { container } = render(HomePage());
    expect(imageBySrc(container, marketingMedia.hero.src)).not.toBeNull();
  });

  it("renders the reviewer workflow media placeholder", () => {
    const { container } = render(HomePage());
    expect(screen.getByText("Reviewer workflow")).toBeInTheDocument();
    expect(imageBySrc(container, marketingMedia.workflow.src)).not.toBeNull();
  });

  it("renders the technical foundation media placeholder", () => {
    const { container } = render(HomePage());
    expect(screen.getByText("Technical foundation")).toBeInTheDocument();
    expect(
      imageBySrc(container, marketingMedia.technicalFoundation.src),
    ).not.toBeNull();
  });

  it("renders the human reviewer boundary media placeholder", () => {
    const { container } = render(HomePage());
    expect(screen.getByText("Human reviewer boundary")).toBeInTheDocument();
    expect(
      imageBySrc(container, marketingMedia.humanReviewBoundary.src),
    ).not.toBeNull();
  });

  it("renders the guided demo journey media placeholder", () => {
    const { container } = render(HomePage());
    expect(screen.getByText("Guided demo journey")).toBeInTheDocument();
    expect(
      imageBySrc(container, marketingMedia.guidedDemoJourney.src),
    ).not.toBeNull();
  });

  it("keeps the Brookside Meadows sample project section", () => {
    render(HomePage());
    expect(
      screen.getByText("Brookside Meadows sample project"),
    ).toBeInTheDocument();
  });
});

describe("HomePage calls to action and links", () => {
  it("keeps Start the demo as a primary call to action", () => {
    const { container } = render(HomePage());
    expect(screen.getAllByText("Start the demo").length).toBeGreaterThan(0);
    // The primary CTA uses the design-system primary button; secondary CTAs use
    // the secondary button.
    expect(container.querySelector("a.btn.btn-primary")).not.toBeNull();
    expect(container.querySelector("a.btn.btn-secondary")).not.toBeNull();
  });

  it("keeps Start Here and Guided Demo links reachable", () => {
    const { container } = render(HomePage());
    expect(container.querySelector('a[href="/start-here"]')).not.toBeNull();
    expect(container.querySelector('a[href="/guided-demo"]')).not.toBeNull();
  });

  it("keeps the important workflow and dashboard links", () => {
    const { container } = render(HomePage());
    for (const href of [
      "/projects",
      "/dashboard",
      "/dashboard/queue",
      "/rule-packs",
      "/deployment-status",
    ]) {
      expect(container.querySelector(`a[href="${href}"]`)).not.toBeNull();
    }
  });
});

describe("HomePage banners stay visible", () => {
  it("keeps the backend status banner in the hero", () => {
    render(HomePage());
    expect(
      screen.getByText(/Checking backend connection/i),
    ).toBeInTheDocument();
  });

  it("keeps the professional boundary banner visible", () => {
    render(HomePage());
    expect(
      screen.getAllByText(/Professional boundary/i).length,
    ).toBeGreaterThan(0);
  });
});

describe("HomePage copy hygiene", () => {
  it("does not contain stale sprint-number copy", () => {
    const { container } = render(HomePage());
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).not.toContain("sprint");
  });

  it("does not dominate the page with long repeated boundary paragraphs", () => {
    // The hero supporting paragraph is intentionally short. Guard against a
    // regression that reintroduces a multi-sentence hero text wall.
    const { container } = render(HomePage());
    const heroParagraph = container.querySelector("section p.max-w-xl");
    expect(heroParagraph).not.toBeNull();
    const sentences = (heroParagraph?.textContent ?? "")
      .split(".")
      .map((s) => s.trim())
      .filter(Boolean);
    expect(sentences.length).toBeLessThanOrEqual(2);
  });

  it("does not expose raw storage paths, keys, tokens, or secrets in the UI", () => {
    const { container } = render(HomePage());
    const text = (container.textContent ?? "").toLowerCase();
    for (const leak of [
      "storage_key",
      "signed_url",
      "bearer ey",
      "password",
      "/home/",
      "secret",
    ]) {
      expect(text).not.toContain(leak);
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

  it("does not use prohibited final-decision wording as a claim in the homepage source", () => {
    // Scan the homepage source rather than rendered output. The rendered page
    // includes the SafetyBoundaryBanner, which intentionally displays forbidden
    // vocabulary as examples of language the system never uses.
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
      "production ready",
      "enterprise ready",
    ]) {
      expect(source).not.toContain(phrase);
    }
  });
});
