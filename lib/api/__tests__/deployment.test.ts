import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { API_BASE_URL } from "@/lib/api";

function read(relativePath: string): string {
  return readFileSync(resolve(process.cwd(), relativePath), "utf8");
}

// A regex that matches a public phase label such as "Phase 1" or "Phase 14".
const PHASE_LABEL = /Phase\s+\d+/;

describe("public surfaces carry no phase chronology", () => {
  it("the README does not present current phase language", () => {
    const readme = read("README.md");
    expect(readme).not.toMatch(PHASE_LABEL);
    expect(readme.toLowerCase()).not.toContain("current phase");
  });

  it("the package.json description has no phase language", () => {
    const pkg = JSON.parse(read("package.json")) as { description: string };
    expect(pkg.description).not.toMatch(PHASE_LABEL);
    expect(pkg.description.toLowerCase()).not.toContain("phase");
  });

  it("the homepage has no public phase badge", () => {
    const homepage = read("app/page.tsx");
    expect(homepage).not.toMatch(PHASE_LABEL);
  });

  it("the navigation has no phase badge", () => {
    const nav = read("components/SiteNav.tsx");
    expect(nav).not.toMatch(PHASE_LABEL);
  });

  it("the product overview leads with capability, not phase numbers", () => {
    const overview = read("docs/PRODUCT_OVERVIEW.md");
    expect(overview).not.toMatch(PHASE_LABEL);
  });
});

describe("Railway deployment readiness", () => {
  it("the deployment guide targets Railway and does not recommend Vercel", () => {
    const guide = read("docs/RAILWAY_DEPLOYMENT_GUIDE.md");
    expect(guide).toContain("Railway");
    expect(guide.toLowerCase()).not.toContain("vercel");
  });

  it("the README does not recommend Vercel as the deployment target", () => {
    const readme = read("README.md").toLowerCase();
    expect(readme).toContain("railway");
    expect(readme).not.toContain("vercel");
  });

  it("the frontend env example documents the API base URL variable", () => {
    const envExample = read(".env.example");
    expect(envExample).toContain("NEXT_PUBLIC_API_BASE_URL");
  });
});

describe("API base URL environment behavior", () => {
  it("defaults to the local backend when the env var is not set", () => {
    // NEXT_PUBLIC_API_BASE_URL is not set in the test environment, so the
    // client falls back to the local backend rather than a hard-coded deploy
    // URL.
    expect(API_BASE_URL).toBe("http://localhost:8000");
  });

  it("the client reads the base URL from NEXT_PUBLIC_API_BASE_URL", () => {
    const client = read("lib/api/client.ts");
    expect(client).toContain("process.env.NEXT_PUBLIC_API_BASE_URL");
    expect(client).not.toContain("https://");
  });
});
