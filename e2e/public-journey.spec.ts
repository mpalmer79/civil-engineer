import { createHash } from "node:crypto";

import { expect, test } from "@playwright/test";

// Public journey: homepage, synthetic disclosure, guided demo, human-review
// boundary, technical overview, proof-of-concept page, artifact downloads,
// and the Civil Engineer AI Guide. No account is required for any of it.

test.describe("public journey", () => {
  test("homepage loads with the synthetic case-study disclosure", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { level: 1 }),
    ).toContainText("Review stormwater submissions");
    await expect(page.locator("body")).toContainText("Brookside Meadows");
    await expect(page.locator("body")).toContainText("synthetic");
  });

  test("guided demo walks to the reviewer handoff boundary", async ({
    page,
  }) => {
    await page.goto("/guided-demo");
    await expect(page.locator("body")).toContainText("Brookside Meadows");
    await expect(page.locator("body")).toContainText(
      "Human reviewers stay responsible",
    );
  });

  test("technical overview links to the proof of concept", async ({
    page,
  }) => {
    await page.goto("/start-here");
    const proofLink = page.getByRole("link", {
      name: "Open the proof of concept",
    });
    await expect(proofLink).toBeVisible();
    await proofLink.click();
    await expect(page).toHaveURL(/\/proof-of-concept$/);
  });

  test("proof-of-concept page shows evidence-backed metrics", async ({
    page,
  }) => {
    await page.goto("/proof-of-concept");
    await expect(
      page.getByRole("heading", {
        name: "Proof of Concept: DXF Intake and Review Support",
      }),
    ).toBeVisible();
    // Metrics come from the structured artifact.
    await expect(page.locator("dd", { hasText: /^168$/ })).toBeVisible();
    await expect(page.locator("body")).toContainText(
      "What this does not prove",
    );
    await expect(page.locator("body")).toContainText("Final plan approval");
    // The consistency alert must not be present on a healthy build.
    await expect(
      page.getByText("Proof artifact consistency check failed"),
    ).toHaveCount(0);
  });

  test("proof-of-concept redirects resolve", async ({ page }) => {
    const first = await page.goto("/proofofconcept");
    expect(first?.url()).toContain("/proof-of-concept");
    const second = await page.goto("/poc");
    expect(second?.url()).toContain("/proof-of-concept");
  });

  test("proof artifacts download with correct hashes", async ({
    page,
    request,
  }) => {
    await page.goto("/proof-of-concept");
    const manifest = await (
      await request.get("/proof-of-concept/dxf/manifest.json")
    ).json();
    expect(manifest.artifacts).toHaveLength(4);
    for (const artifact of manifest.artifacts) {
      const response = await request.get(artifact.download_route);
      expect(response.status()).toBe(200);
      expect(response.headers()["content-type"]).toBe(artifact.content_type);
      const body = await response.body();
      expect(body.byteLength).toBe(artifact.file_size_bytes);
      const digest = createHash("sha256").update(body).digest("hex");
      expect(digest).toBe(artifact.sha256);
    }
  });

  test("unknown proof artifact and traversal attempts are rejected", async ({
    request,
  }) => {
    expect(
      (await request.get("/api/proof-of-concept/download/nope")).status(),
    ).toBe(404);
    expect(
      (
        await request.get(
          "/api/proof-of-concept/download/..%2F..%2Fpackage.json",
        )
      ).status(),
    ).toBe(404);
  });

  test("the guide answers a proof-of-concept question locally", async ({
    page,
  }) => {
    await page.goto("/proof-of-concept");
    // Block all network egress except the app itself: the guide must answer
    // without any outside API.
    await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (route) => route.abort());
    await page
      .getByRole("button", { name: "Civil Engineer AI Guide" })
      .click();
    const input = page.getByLabel(/ask/i).or(page.locator("#ceai-guide-input"));
    await input.first().fill("what is the proof of concept");
    await input.first().press("Enter");
    const panel = page.locator("#ceai-guide-panel");
    await expect(panel).toContainText(/synthetic|proof/i, { timeout: 15000 });
  });
});
