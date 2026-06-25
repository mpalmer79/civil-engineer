import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function read(relativePath: string): string {
  return readFileSync(resolve(process.cwd(), relativePath), "utf8");
}

// Public surfaces that carry CAD/DXF capability copy.
const CAD_COPY_SOURCES = [
  "app/page.tsx",
  "app/cad-review/page.tsx",
  "app/cad-intake/page.tsx",
  "app/sheet-viewer/page.tsx",
  "components/CadReviewClient.tsx",
];

// Phrases that wrongly imply DXF parsing is absent from the product. CAD Intake
// parses real DXF files, so none of these should appear in public copy.
const DXF_ABSENCE_PHRASES = [
  "no DXF parsing",
  "no live CAD parsing",
  "not live CAD parsing",
  "does not parse real DXF",
  "seeded CAD-aware metadata only",
  "without processing real CAD",
  "not extracted from DWG or DXF",
];

describe("CAD/DXF copy reflects current DXF support", () => {
  it("does not claim DXF parsing is absent on any public page", () => {
    for (const source of CAD_COPY_SOURCES) {
      const text = read(source).toLowerCase();
      for (const phrase of DXF_ABSENCE_PHRASES) {
        expect(text).not.toContain(phrase.toLowerCase());
      }
    }
  });

  it("locates real DXF parsing in CAD Intake consistently across pages", () => {
    const home = read("app/page.tsx");
    expect(home).toContain("CAD Intake");
    expect(home).toContain("DXF");

    const cadReview = read("app/cad-review/page.tsx");
    expect(cadReview).toContain("CAD Intake");
    expect(cadReview.toLowerCase()).toContain("dxf");

    const cadIntake = read("app/cad-intake/page.tsx");
    expect(cadIntake.toLowerCase()).toContain("dxf");
    // CAD Intake is where extraction happens.
    expect(cadIntake.toLowerCase()).toMatch(/parse|parsing|extract/);
  });

  it("keeps the professional boundary on the CAD review page", () => {
    const cadReview = read("app/cad-review/page.tsx").toLowerCase();
    expect(cadReview).toContain("does not parse dwg");
    expect(cadReview).toMatch(/does not.*verify cad|verify cad/);
  });
});

describe("no prohibited final-decision language in updated copy", () => {
  const sources = [
    "app/page.tsx",
    "app/cad-review/page.tsx",
    "app/sheet-viewer/page.tsx",
    "app/guided-demo/page.tsx",
    "components/GuidedDemoThread.tsx",
  ];

  // Affirmative final-decision claims that would breach the review-support
  // boundary. These differ from boundary disclaimers like "does not approve".
  const FORBIDDEN_AFFIRMATIONS = [
    "design validated",
    "plan approved",
    "fully compliant",
    "is certified",
    "are certified",
    "marked safe",
    "passed review",
  ];

  it("introduces no affirmative approval, certification, or safety claims", () => {
    for (const source of sources) {
      const text = read(source).toLowerCase();
      for (const phrase of FORBIDDEN_AFFIRMATIONS) {
        expect(text).not.toContain(phrase);
      }
    }
  });
});
