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

const RECRUITER_DOCS = [
  "docs/recruiter-walkthrough.md",
  "docs/recruiter-walkthrough-storyboard.md",
  "docs/architecture-overview.md",
  "docs/real-vs-mocked.md",
  "docs/synthetic-demo-data.md",
  "docs/technical-decisions.md",
  "docs/test-summary.md",
];

describe("Recruiter documentation exists", () => {
  it("ships every recruiter and technical review doc", () => {
    for (const doc of RECRUITER_DOCS) {
      expect(existsSync(join(root, doc)), doc).toBe(true);
    }
  });

  it("links every recruiter doc from the README technical review section", () => {
    const readme = read("README.md");
    expect(readme).toContain("## Technical Review Links");
    for (const doc of RECRUITER_DOCS.filter(
      (d) => d !== "docs/recruiter-walkthrough-storyboard.md",
    )) {
      expect(readme, doc).toContain(`(${doc})`);
    }
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

  it("references the visual walkthrough only when the file exists", () => {
    const readme = read("README.md");
    const gifPath = "public/images/civil-engineer/recruiter-walkthrough.gif";
    if (readme.includes("recruiter-walkthrough.gif")) {
      expect(existsSync(join(root, gifPath))).toBe(true);
      expect(readme).toContain("## Visual Walkthrough");
    }
  });
});

describe("Recruiter docs language hygiene", () => {
  it("contains no attribution tokens", () => {
    for (const doc of RECRUITER_DOCS) {
      const text = read(doc).toLowerCase();
      for (const token of ATTRIBUTION_TOKENS) {
        expect(text, `${doc} must not contain "${token}"`).not.toContain(token);
      }
    }
  });

  it("contains no em dashes", () => {
    for (const doc of RECRUITER_DOCS) {
      expect(read(doc), doc).not.toContain("—");
    }
  });

  it("keeps the review-support boundary in the walkthrough and architecture docs", () => {
    const walkthrough = read("docs/recruiter-walkthrough.md").toLowerCase();
    expect(walkthrough).toContain("does not approve plans");
    expect(walkthrough).toContain("synthetic demo data");

    const architecture = read("docs/architecture-overview.md").toLowerCase();
    expect(architecture).toContain("human reviewer");
    expect(architecture).toContain("no approve action");
  });

  it("labels demo data honestly in the real-vs-mocked map", () => {
    const map = read("docs/real-vs-mocked.md");
    expect(map).toContain("Seeded demo");
    expect(map).toContain("Static prototype");
    expect(map).toContain("Simulated");
    expect(map.toLowerCase()).toContain("live ai disabled by default");
  });

  it("states that Brookside Meadows and the Town of Hartwell are fictional", () => {
    const data = read("docs/synthetic-demo-data.md").toLowerCase();
    expect(data).toContain("synthetic demo data");
    expect(data).toContain("town of hartwell is fictional");
    expect(data).toContain("does not make real approval decisions");
  });
});
