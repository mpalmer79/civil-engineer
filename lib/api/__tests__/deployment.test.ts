import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";

import { API_BASE_URL, BACKEND_ORIGIN, getProject } from "@/lib/api";

function read(relativePath: string): string {
  return readFileSync(resolve(process.cwd(), relativePath), "utf8");
}

// Returns the assigned value of every NEXT_PUBLIC_API_BASE_URL=... occurrence in
// the given text, so a test can confirm example URLs are the origin only.
function apiBaseUrlExamples(text: string): string[] {
  const matches = text.matchAll(/NEXT_PUBLIC_API_BASE_URL=(\S+)/g);
  return Array.from(matches, (m) => m[1]);
}

afterEach(() => {
  vi.restoreAllMocks();
});

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
    const overview = read("docs/PRODUCT.md");
    expect(overview).not.toMatch(PHASE_LABEL);
  });
});

describe("Railway deployment readiness", () => {
  it("the deployment guide targets Railway and does not recommend Vercel", () => {
    const guide = read("docs/DEPLOYMENT.md");
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

  it("documents the backend health and project test routes", () => {
    const guide = read("docs/DEPLOYMENT.md");
    expect(guide).toContain("/health");
    expect(guide).toContain("/api/v1/projects/proj_brookside_meadows");
    // A 404 on the backend root is documented as not necessarily a failure.
    expect(guide.toLowerCase()).toContain("not necessarily a failure");
  });

  it("the README documents the backend health route", () => {
    const readme = read("README.md");
    expect(readme).toContain("/health");
    expect(readme).toContain("/api/v1/projects/proj_brookside_meadows");
  });
});

describe("NEXT_PUBLIC_API_BASE_URL example hygiene", () => {
  const sources = [
    ".env.example",
    "docs/DEPLOYMENT.md",
    "README.md",
  ];

  it("never includes /api/v1 in a base URL example value", () => {
    for (const source of sources) {
      const examples = apiBaseUrlExamples(read(source));
      expect(examples.length).toBeGreaterThan(0);
      for (const value of examples) {
        expect(value).not.toContain("/api/v1");
        expect(value).not.toContain("/api");
      }
    }
  });

  it("documents that the base URL is the backend origin only", () => {
    const envExample = read(".env.example");
    expect(envExample.toLowerCase()).toContain("origin only");
    const guide = read("docs/DEPLOYMENT.md");
    expect(guide).toContain("origin");
  });
});

describe("API client path construction", () => {
  it("appends an /api/v1 path to the base URL when calling the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        project_id: "proj_brookside_meadows",
        project_name: "Brookside Meadows",
        project_type: "subdivision",
        location_context: "",
        jurisdiction: "",
        review_type: "",
        review_domain: "",
        acreage: 0,
        disturbed_area: 0,
        proposed_lots: 0,
        status: "",
        summary: "",
        site_conditions: [],
        proposed_improvements: [],
        known_constraints: [],
      }),
    } as Response);
    globalThis.fetch = fetchMock;

    await getProject();

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toBe(
      `${API_BASE_URL}/api/v1/projects/proj_brookside_meadows`,
    );
    // The base URL itself must not already carry the /api/v1 prefix, or the
    // call would double it.
    expect(API_BASE_URL).not.toContain("/api/v1");
  });
});

describe("API base URL environment behavior", () => {
  it("uses the same-origin proxy in the browser and the backend origin default on the server", () => {
    // Tests run in jsdom (a browser context), where all API calls go through
    // the same-origin proxy so the HttpOnly session cookie can authenticate
    // them. The server-side origin falls back to the local backend.
    expect(API_BASE_URL).toBe("/api/backend");
    expect(BACKEND_ORIGIN).toBe("http://localhost:8000");
  });

  it("the client reads the base URL from NEXT_PUBLIC_API_BASE_URL", () => {
    const client = read("lib/api/client.ts");
    expect(client).toContain("process.env.NEXT_PUBLIC_API_BASE_URL");
    expect(client).not.toContain("https://");
  });
});
