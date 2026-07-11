import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// Automated accessibility release gate. Serious and critical Axe violations
// fail the build on the public pages below. Moderate and minor findings are
// tracked in docs/100_SCORE_TRANSFORMATION.md rather than gating.

const PUBLIC_PAGES = [
  { name: "homepage", path: "/" },
  { name: "guided demo", path: "/guided-demo" },
  { name: "proof of concept", path: "/proof-of-concept" },
  { name: "technical overview", path: "/start-here" },
  { name: "login", path: "/login" },
  { name: "registration", path: "/register" },
  { name: "projects", path: "/projects" },
  { name: "brookside project", path: "/projects/proj_brookside_meadows" },
  { name: "cad intake", path: "/projects/proj_brookside_meadows/cad" },
  { name: "findings", path: "/projects/proj_brookside_meadows/findings" },
  { name: "documents", path: "/projects/proj_brookside_meadows/documents" },
] as const;

for (const target of PUBLIC_PAGES) {
  test(`axe: ${target.name} has no serious or critical violations`, async ({
    page,
  }) => {
    await page.goto(target.path);
    await page.waitForLoadState("networkidle");
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    const gating = results.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact ?? ""),
    );
    // Include full node detail in the assertion payload so a CI failure
    // names the exact elements without needing the trace artifact.
    expect(
      gating.map((violation) => ({
        id: violation.id,
        impact: violation.impact,
        help: violation.help,
        nodes: violation.nodes.map((node) => ({
          target: node.target.join(" "),
          summary: node.failureSummary,
          html: node.html.slice(0, 200),
        })),
      })),
    ).toEqual([]);
  });
}
