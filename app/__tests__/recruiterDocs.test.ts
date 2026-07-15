import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const root = process.cwd();

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

// Attribution tokens assembled from fragments so the literal strings are never
// stored verbatim while still asserting their absence in shipped docs.
const ATTRIBUTION_TOKENS = [
  ["generated", "by"].join(" "),
  ["claude", "code"].join(" "),
  ["claude.ai", "code"].join("/"),
  ["co-authored", "by"].join("-"),
];

// The canonical, current-state documentation set after consolidation. These are
// the authoritative documents the README and the docs index point to.
const CANONICAL_DOCS = [
  "docs/README.md",
  "docs/PRODUCT.md",
  "docs/ARCHITECTURE.md",
  "docs/DOMAIN_MODEL.md",
  "docs/SECURITY.md",
  "docs/OPERATIONS.md",
  "docs/DEPLOYMENT.md",
  "docs/TESTING.md",
  "docs/API.md",
  "docs/DXF_VALIDATION.md",
  "docs/REFERENCE_PROJECT.md",
  "docs/ROADMAP.md",
];

describe("Canonical documentation exists", () => {
  it("ships every canonical current-state document", () => {
    for (const doc of CANONICAL_DOCS) {
      expect(existsSync(join(root, doc)), doc).toBe(true);
    }
  });

  it("links every canonical document from the README documentation section", () => {
    const readme = read("README.md");
    expect(readme).toContain("## Documentation");
    for (const doc of CANONICAL_DOCS.filter((d) => d !== "docs/README.md")) {
      expect(readme, doc).toContain(`(${doc})`);
    }
  });

  it("archives the superseded recruiter and phase material", () => {
    expect(existsSync(join(root, "docs/archive/README.md"))).toBe(true);
    // The recruiter walkthrough was folded and archived, not kept active.
    expect(existsSync(join(root, "docs/recruiter-walkthrough.md"))).toBe(false);
  });
});

describe("README links resolve to real files", () => {
  it("has no relative link pointing at a missing file", () => {
    const readme = read("README.md");
    const targets = [...readme.matchAll(/\]\(([^)]+)\)/g)]
      .map((m) => m[1])
      .filter(
        (l) =>
          !l.startsWith("http") && !l.startsWith("#") && !l.startsWith("mailto"),
      )
      .map((l) => l.split("#")[0]);
    expect(targets.length).toBeGreaterThan(0);
    for (const target of targets) {
      expect(existsSync(join(root, target)), target).toBe(true);
    }
  });
});

describe("Canonical docs language hygiene", () => {
  it("contains no attribution tokens", () => {
    for (const doc of CANONICAL_DOCS) {
      const text = read(doc).toLowerCase();
      for (const token of ATTRIBUTION_TOKENS) {
        expect(text, `${doc} must not contain "${token}"`).not.toContain(token);
      }
    }
  });

  it("contains no em dashes", () => {
    for (const doc of CANONICAL_DOCS) {
      expect(read(doc), doc).not.toContain("\u2014");
    }
  });

  it("keeps the review-support boundary in the product and security docs", () => {
    const product = read("docs/PRODUCT.md").toLowerCase();
    expect(product).toContain("does not approve plans");
    expect(product).toContain("review-support");
    expect(product).toContain("no action named approve");

    const security = read("docs/SECURITY.md").toLowerCase();
    expect(security).toContain("human reviewer");
    expect(security).toContain("does not approve plans");
  });

  it("labels the reference project honestly", () => {
    const product = read("docs/PRODUCT.md");
    expect(product).toContain("Seeded demo");
    expect(product).toContain("Simulated");
    expect(product).toContain("Static prototype");
    expect(product.toLowerCase()).toContain("live ai disabled by default");

    const reference = read("docs/REFERENCE_PROJECT.md").toLowerCase();
    expect(reference).toContain("synthetic demo data");
    expect(reference).toContain("town of hartwell is fictional");
    expect(reference).toContain("does not make real approval decisions");
  });
});
