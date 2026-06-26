import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";

import { API_BASE_URL, getReviewCycles } from "@/lib/api";

function read(relativePath: string): string {
  return readFileSync(resolve(process.cwd(), relativePath), "utf8");
}

// All NEXT_PUBLIC_API_BASE_URL assignment values across a file.
function apiBaseAssignments(text: string): string[] {
  return [...text.matchAll(/^NEXT_PUBLIC_API_BASE_URL=(.*)$/gm)].map((m) =>
    m[1].trim(),
  );
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

describe("NEXT_PUBLIC_API_BASE_URL is documented as the backend origin only", () => {
  it("the env example assigns the backend origin without /api/v1", () => {
    const values = apiBaseAssignments(read(".env.example"));
    expect(values.length).toBeGreaterThan(0);
    for (const value of values) {
      expect(value).not.toContain("/api");
    }
  });

  it("the deployment guide example assigns the backend origin without /api/v1", () => {
    const values = apiBaseAssignments(read("docs/RAILWAY_DEPLOYMENT_GUIDE.md"));
    expect(values.length).toBeGreaterThan(0);
    for (const value of values) {
      expect(value).not.toContain("/api");
    }
  });

  it("the deployment guide explains the base URL must not include /api/v1", () => {
    const guide = read("docs/RAILWAY_DEPLOYMENT_GUIDE.md");
    expect(guide).toContain("/api/v1");
    expect(guide.toLowerCase()).toContain("appends");
  });
});

describe("backend test URLs are documented", () => {
  it("the deployment guide documents /health and the project API route", () => {
    const guide = read("docs/RAILWAY_DEPLOYMENT_GUIDE.md");
    expect(guide).toContain("/health");
    expect(guide).toContain("/api/v1/projects/proj_brookside_meadows");
  });

  it("the deployment guide notes a 404 on the backend root is not a failure", () => {
    const guide = read("docs/RAILWAY_DEPLOYMENT_GUIDE.md").toLowerCase();
    expect(guide).toContain("404");
    expect(guide).toContain("root");
  });
});

describe("frontend API client appends /api/v1 paths", () => {
  it("calls the backend under /api/v1 from the base origin", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    } as Response);
    globalThis.fetch = fetchSpy;
    await getReviewCycles();
    const url = fetchSpy.mock.calls[0][0] as string;
    expect(url.startsWith(`${API_BASE_URL}/api/v1/`)).toBe(true);
    expect(url).toContain("/api/v1/projects/proj_brookside_meadows/review-cycles");
    // The base URL itself must not already include /api, or the path doubles.
    expect(API_BASE_URL).not.toContain("/api");
  });
});

describe("CAD copy reflects the current product", () => {
  const cadPages = [
    "app/page.tsx",
    "app/cad-intake/page.tsx",
    "app/cad-review/page.tsx",
    "app/plan-sheets/page.tsx",
    "app/sheet-viewer/page.tsx",
  ];

  it("no public CAD page claims DXF parsing is absent", () => {
    const forbidden = [
      "no dxf parsing",
      "not live cad parsing",
      "does not parse real dxf",
      "seeded cad-aware metadata only",
      "does not parse dwg or dxf",
      "without processing real cad",
    ];
    for (const page of cadPages) {
      const text = read(page).toLowerCase();
      for (const phrase of forbidden) {
        expect(text, `${page} should not contain "${phrase}"`).not.toContain(
          phrase,
        );
      }
    }
  });

  it("the homepage states real DXF parsing lives in CAD Intake", () => {
    const home = read("app/page.tsx");
    expect(home).toContain("CAD Intake");
    expect(home.toLowerCase()).toContain("dxf");
    expect(home.toLowerCase()).toMatch(/dxf (upload|metadata|file)/);
  });

  it("CAD Review points real DXF parsing to CAD Intake", () => {
    const cadReview = read("app/cad-review/page.tsx");
    expect(cadReview).toContain("CAD Intake");
  });

  it("CAD Intake describes real DXF upload and parsing", () => {
    const cadIntake = read("app/cad-intake/page.tsx").toLowerCase();
    expect(cadIntake).toContain("dxf");
    expect(cadIntake).toMatch(/upload|parse/);
  });
});

describe("guided demo thread copy", () => {
  it("the demo thread covers the selected infiltration finding end to end", () => {
    const thread = read("components/GuidedDemoThread.tsx").toLowerCase();
    expect(thread).toContain("infiltration");
    expect(thread).toContain("groundwater");
    for (const step of [
      "checklist requirement",
      "finding",
      "source evidence",
      "review packet item",
      "workflow board item",
      "draft response",
      "human-review boundary",
    ]) {
      expect(thread).toContain(step);
    }
  });

  it("the demo thread uses no prohibited final-decision language", () => {
    const thread = read("components/GuidedDemoThread.tsx").toLowerCase();
    const demoRoute = read("app/demo/page.tsx").toLowerCase();
    const prohibited = [
      "approved",
      "certified",
      "verified",
      "compliant",
      "design validated",
    ];
    for (const word of prohibited) {
      expect(thread).not.toContain(word);
      expect(demoRoute).not.toContain(word);
    }
  });
});
