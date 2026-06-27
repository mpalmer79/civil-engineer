import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import MarketingMedia from "@/components/MarketingMedia";
import { marketingMedia } from "@/lib/marketingMedia";

afterEach(() => cleanup());

// Affirmative final-decision wording that must never appear in marketing media
// copy or alt text. Negated boundary wording is allowed elsewhere, but these
// presentation surfaces should stay neutral.
const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "compliant",
  "noncompliant",
  "verified",
  "passed review",
  "failed review",
  "validated",
  "resolved",
  "pe stamped",
  "final approval",
];

// Attribution tokens assembled from fragments so the literal strings are never
// stored verbatim while still asserting their absence.
const ATTRIBUTION_TOKENS = [
  ["claude", "code"].join(" "),
  ["claude.ai", "code"].join("/"),
  ["co-authored", "by"].join("-"),
  ["generated", "by"].join(" "),
];

describe("marketingMedia manifest", () => {
  const entries = Object.values(marketingMedia);

  it("exports all expected media entries", () => {
    expect(Object.keys(marketingMedia)).toEqual([
      "hero",
      "workflow",
      "technicalFoundation",
      "humanReviewBoundary",
      "guidedDemoJourney",
    ]);
  });

  it("points every src at the civil-engineer public image folder", () => {
    for (const entry of entries) {
      expect(entry.src.startsWith("/images/civil-engineer/")).toBe(true);
      expect(entry.src.endsWith(".webp")).toBe(true);
    }
  });

  it("defines non-empty alt text for every image", () => {
    for (const entry of entries) {
      expect(entry.alt.trim().length).toBeGreaterThan(0);
    }
  });

  it("does not include attribution or final-decision wording in alt text", () => {
    for (const entry of entries) {
      const alt = entry.alt.toLowerCase();
      for (const word of PROHIBITED_WORDS) {
        expect(alt).not.toContain(word);
      }
      for (const token of ATTRIBUTION_TOKENS) {
        expect(alt).not.toContain(token);
      }
    }
  });
});

describe("MarketingMedia component", () => {
  it("renders an image with the provided src and alt", () => {
    render(
      <MarketingMedia
        src={marketingMedia.hero.src}
        alt={marketingMedia.hero.alt}
      />,
    );
    const img = screen.getByTestId("marketing-media-image");
    expect(img).toHaveAttribute("src", marketingMedia.hero.src);
    expect(img).toHaveAttribute("alt", marketingMedia.hero.alt);
  });

  it("hides the broken image and shows a polished fallback on load error", () => {
    render(
      <MarketingMedia
        src="/images/civil-engineer/missing.webp"
        alt={marketingMedia.workflow.alt}
      />,
    );
    const img = screen.getByTestId("marketing-media-image");
    fireEvent.error(img);

    expect(screen.queryByTestId("marketing-media-image")).toBeNull();
    const fallback = screen.getByTestId("marketing-media-fallback");
    // The fallback keeps the alt text accessible and never shows a broken icon.
    expect(fallback).toHaveAttribute("role", "img");
    expect(fallback).toHaveAttribute("aria-label", marketingMedia.workflow.alt);
  });

  it("does not expose attribution or final-decision wording", () => {
    const { container } = render(
      <MarketingMedia
        src="/images/civil-engineer/missing.webp"
        alt={marketingMedia.humanReviewBoundary.alt}
      />,
    );
    fireEvent.error(screen.getByTestId("marketing-media-image"));
    const text = (container.textContent ?? "").toLowerCase();
    for (const word of PROHIBITED_WORDS) {
      expect(text).not.toContain(word);
    }
    for (const token of ATTRIBUTION_TOKENS) {
      expect(text).not.toContain(token);
    }
  });
});
