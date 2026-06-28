import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const root = process.cwd();

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

// Attribution tokens assembled from fragments so the literal strings are never
// stored verbatim while still asserting their absence in shipped docs/copy.
const ATTRIBUTION_TOKENS = [
  ["generated", "by"].join(" "),
  ["claude", "code"].join(" "),
  ["claude.ai", "code"].join("/"),
  ["co-authored", "by"].join("-"),
];

// Affirmative final-decision claims that must never appear as a product promise
// in operational/admin/release surfaces. Negative boundary statements are fine.
const PROHIBITED_PROMISES = [
  "plan approved",
  "design validated",
  "fully compliant",
  "passes review",
  "passed review",
  "guaranteed compliance",
  "meets all requirements",
  "marked safe",
];

describe("Release docs exist", () => {
  it("ships the release readiness and pilot checklist docs", () => {
    expect(existsSync(join(root, "docs/RELEASE_READINESS.md"))).toBe(true);
    expect(existsSync(join(root, "docs/PILOT_RELEASE_CHECKLIST.md"))).toBe(true);
  });

  it("ships the pilot operations and design-partner outreach docs", () => {
    expect(existsSync(join(root, "docs/PILOT_OPERATIONS.md"))).toBe(true);
    expect(existsSync(join(root, "docs/DESIGN_PARTNER_OUTREACH.md"))).toBe(true);
  });

  it("ships the pilot release verification script and npm script", () => {
    expect(existsSync(join(root, "scripts/verify-pilot-release.mjs"))).toBe(true);
    expect(read("package.json")).toContain("verify:pilot");
  });

  it("documents the production-posture flags and public route allowlist", () => {
    const readiness = read("docs/RELEASE_READINESS.md");
    expect(readiness).toContain("AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS");
    expect(readiness).toContain("AUTH_DEMO_MODE");
    expect(readiness).toContain("AUTH_ALLOW_PUBLIC_DEMO");
    expect(readiness.toLowerCase()).toContain("public route allowlist");
  });

  it("does not duplicate the release docs", () => {
    // A single canonical readiness doc and a single checklist doc.
    expect(existsSync(join(root, "docs/RELEASE_READINESS.md"))).toBe(true);
    expect(existsSync(join(root, "docs/RELEASE-READINESS.md"))).toBe(false);
  });

  it("states the honest pilot limitations", () => {
    const readiness = read("docs/RELEASE_READINESS.md").toLowerCase();
    expect(readiness).toContain("billing");
    expect(readiness).toContain("sqlite");
    expect(readiness).toContain("design-partner pilot");
    expect(readiness).toContain("live ai");
  });

  it("lists required environment variables in the checklist", () => {
    const checklist = read("docs/PILOT_RELEASE_CHECKLIST.md");
    expect(checklist).toContain("AUTH_SECRET_KEY");
    expect(checklist).toContain("DATABASE_URL");
    expect(checklist).toContain("NEXT_PUBLIC_API_BASE_URL");
  });
});

describe("Release routes exist", () => {
  it("ships the workspace and pilot admin routes", () => {
    expect(existsSync(join(root, "app/workspace/page.tsx"))).toBe(true);
    expect(existsSync(join(root, "app/workspace/settings/page.tsx"))).toBe(true);
    expect(existsSync(join(root, "app/admin/pilot-requests/page.tsx"))).toBe(true);
  });
});

describe("No attribution footer in release docs and operational copy", () => {
  const files = [
    "docs/RELEASE_READINESS.md",
    "docs/PILOT_RELEASE_CHECKLIST.md",
    "docs/PILOT_OPERATIONS.md",
    "docs/DESIGN_PARTNER_OUTREACH.md",
    "app/workspace/page.tsx",
    "app/admin/pilot-requests/page.tsx",
    "components/PilotReleaseNote.tsx",
  ];

  it("contains no generated-by or attribution tokens", () => {
    for (const file of files) {
      const text = read(file).toLowerCase();
      for (const token of ATTRIBUTION_TOKENS) {
        expect(text).not.toContain(token);
      }
    }
  });
});

describe("No prohibited final-decision claims in operational copy", () => {
  const files = [
    "app/workspace/page.tsx",
    "app/workspace/settings/page.tsx",
    "app/admin/pilot-requests/page.tsx",
    "components/PilotReleaseNote.tsx",
  ];

  it("uses review-support language only", () => {
    for (const file of files) {
      const text = read(file).toLowerCase();
      for (const phrase of PROHIBITED_PROMISES) {
        expect(text).not.toContain(phrase);
      }
    }
  });

  it("does not present billing or subscriptions as active", () => {
    const settings = read("app/workspace/settings/page.tsx").toLowerCase();
    expect(settings).not.toContain("billing is active");
    expect(settings).not.toContain("subscription active");
    expect(settings).toContain("coming later");
  });
});
