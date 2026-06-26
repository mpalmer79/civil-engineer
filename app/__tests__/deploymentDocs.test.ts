import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const root = process.cwd();

function readDoc(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

// Lines that assign NEXT_PUBLIC_API_BASE_URL, used to confirm the example value
// is the backend origin only with no /api/v1 path. Prose that mentions /api/v1
// to warn against it is intentionally not matched.
function apiBaseUrlAssignments(content: string): string[] {
  return content
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("NEXT_PUBLIC_API_BASE_URL="));
}

describe("Railway deployment guide", () => {
  const guide = readDoc("docs/RAILWAY_DEPLOYMENT_GUIDE.md");

  it("explains that the frontend must be redeployed after the backend URL changes", () => {
    expect(guide).toMatch(/redeploy/i);
    expect(guide.toLowerCase()).toContain(
      "must be redeployed after",
    );
  });

  it("notes that a frontend build can appear stale without a redeploy from latest main", () => {
    expect(guide.toLowerCase()).toContain("stale");
    expect(guide.toLowerCase()).toContain("latest");
  });

  it("uses the backend origin only for the NEXT_PUBLIC_API_BASE_URL example", () => {
    const assignments = apiBaseUrlAssignments(guide);
    expect(assignments.length).toBeGreaterThan(0);
    for (const line of assignments) {
      expect(line).not.toContain("/api/v1");
    }
  });
});

describe("Live site verification doc", () => {
  const doc = readDoc("docs/LIVE_SITE_VERIFICATION.md");

  it("lists the core manual live-site checks", () => {
    expect(doc).toContain("https://civil-engineer.up.railway.app/");
    expect(doc.toLowerCase()).toContain("backend connection banner");
    expect(doc).toContain("Projects");
    expect(doc).toContain("Rule Packs");
    expect(doc).toContain("Organizations");
  });

  it("warns against final-decision and attribution language in the live site", () => {
    expect(doc.toLowerCase()).toContain("final approval");
    expect(doc.toLowerCase()).toContain("generated-by attribution");
  });

  it("keeps the NEXT_PUBLIC_API_BASE_URL guidance as backend origin only", () => {
    expect(doc.toLowerCase()).toContain("backend origin only");
    const assignments = apiBaseUrlAssignments(doc);
    for (const line of assignments) {
      expect(line).not.toContain("/api/v1");
    }
  });
});
