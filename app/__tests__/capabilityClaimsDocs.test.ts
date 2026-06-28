import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const root = process.cwd();

function readDoc(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

// Phase 1C capability claims audit and Phase 2A tenant isolation audit. These
// tests guard the documented capability wording against drift and confirm the
// audit document ships. They reflect the code-checked reality: real DXF parsing
// (ezdxf) and PDF text-layer indexing (pypdf), with no DWG, GIS, or OCR.

describe("SaaS positioning capability claims", () => {
  const positioning = readDoc("docs/SAAS_POSITIONING.md").toLowerCase();

  it("does not claim DXF parsing is absent", () => {
    for (const phrase of [
      "no real pdf, dwg, dxf, or gis parsing",
      "no real dxf parsing",
      "does not parse real dxf",
    ]) {
      expect(positioning).not.toContain(phrase);
    }
  });

  it("states that real DXF parsing and PDF text-layer indexing are implemented", () => {
    expect(positioning).toContain("ezdxf");
    expect(positioning).toContain("pypdf");
    expect(positioning).toContain("text-layer");
  });

  it("is honest that OCR, DWG, and GIS are not supported", () => {
    expect(positioning).toContain("ocr");
    expect(positioning).toContain("dwg");
    expect(positioning).toContain("gis");
  });

  it("keeps live AI disabled by default in the stated capabilities", () => {
    expect(positioning).toContain("disabled by default");
  });

  it("does not present seeded data as extracted from a real submission", () => {
    expect(positioning).toContain("not presented as extracted from a real submission");
  });
});

describe("Tenant isolation audit document", () => {
  it("ships docs/TENANT_ISOLATION_AUDIT.md", () => {
    expect(existsSync(join(root, "docs/TENANT_ISOLATION_AUDIT.md"))).toBe(true);
  });

  it("documents the public demo exception and deferred hardening honestly", () => {
    const audit = readDoc("docs/TENANT_ISOLATION_AUDIT.md").toLowerCase();
    expect(audit).toContain("demo_public");
    expect(audit).toContain("deferred");
    // It must not overclaim production-grade isolation.
    expect(audit).toContain("does not claim production-grade tenant isolation");
  });
});

describe("Roadmap is not duplicated", () => {
  it("has exactly one SaaS roadmap document", () => {
    const docs = readdirSync(join(root, "docs"));
    const roadmaps = docs.filter(
      (name) => /saas.*roadmap/i.test(name) || /roadmap.*saas/i.test(name),
    );
    expect(roadmaps).toEqual(["civil-engineer-ai-saas-roadmap.md"]);
  });
});
