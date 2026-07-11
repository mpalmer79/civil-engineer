import { expect, test } from "@playwright/test";

// Brookside visual system: the conceptual aerial on Start Here, Proof of
// Concept, and the Guided Demo cover, the Projects placement boundary, and
// the social preview metadata that link previews read.

const AERIAL_ALT =
  "Conceptual aerial visualization of the synthetic Brookside Meadows residential subdivision surrounding a stormwater pond.";
const DISCLOSURE =
  "Synthetic case-study visualization. Not a real project, survey, approved design, or constructed development.";

test.describe("brookside visual system", () => {
  test("start here shows the aerial, disclosure, and both actions", async ({
    page,
  }) => {
    await page.goto("/start-here");
    const section = page.locator("section", {
      hasText: "What is Brookside Meadows?",
    });
    await expect(section.getByAltText(AERIAL_ALT)).toBeVisible();
    await expect(section.getByText(DISCLOSURE)).toBeVisible();
    await expect(
      section.getByRole("link", { name: "Start Guided Demo" }),
    ).toBeVisible();
    await expect(
      section.getByRole("link", { name: "Open Brookside Meadows" }),
    ).toBeVisible();
  });

  test("start here stacks the image above the text on mobile", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto("/start-here");
    const image = page.getByAltText(AERIAL_ALT);
    await image.scrollIntoViewIfNeeded();
    const heading = page.getByRole("heading", {
      name: "What is Brookside Meadows?",
    });
    const imageBox = await image.boundingBox();
    const headingBox = await heading.boundingBox();
    expect(imageBox).not.toBeNull();
    expect(headingBox).not.toBeNull();
    expect((imageBox as { y: number }).y).toBeLessThan(
      (headingBox as { y: number }).y,
    );
  });

  test("proof of concept shows the aerial with the DXF distinction", async ({
    page,
  }) => {
    await page.goto("/proof-of-concept");
    await expect(page.getByAltText(AERIAL_ALT)).toBeVisible();
    await expect(
      page.getByText(
        "The downloadable DXF is a separately generated test drawing used to exercise the real upload and parsing pipeline.",
      ),
    ).toBeVisible();
  });

  test("guided demo shows the cover with the disclosure and a reachable first action", async ({
    page,
  }) => {
    await page.goto("/guided-demo");
    await expect(
      page.getByRole("heading", { name: "Brookside Meadows Guided Review" }),
    ).toBeVisible();
    await expect(page.getByText(DISCLOSURE)).toBeVisible();
    await expect(page.getByAltText(AERIAL_ALT)).toBeVisible();
    // The first tour step link is still present and usable below the cover.
    await expect(
      page.locator('a[href="/projects/proj_brookside_meadows/cad"]').first(),
    ).toBeVisible();
  });

  test("projects reserves the aerial for the Brookside demo card", async ({
    page,
  }) => {
    await page.goto("/projects");
    await page.waitForLoadState("networkidle");
    // Exactly one Brookside aerial: the seeded demo card. Real project rows
    // never render it.
    await expect(page.getByAltText(AERIAL_ALT)).toHaveCount(1);
  });

  test("homepage exposes the social preview metadata", async ({ page }) => {
    await page.goto("/");
    const ogImage = page.locator('meta[property="og:image"]');
    await expect(ogImage).toHaveAttribute(
      "content",
      /^https:\/\/.+brookside-social-preview\.webp$/,
    );
    await expect(
      page.locator('meta[property="og:image:width"]'),
    ).toHaveAttribute("content", "1200");
    await expect(
      page.locator('meta[property="og:image:height"]'),
    ).toHaveAttribute("content", "630");
    await expect(
      page.locator('meta[property="og:image:alt"]'),
    ).toHaveAttribute("content", AERIAL_ALT);
    await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute(
      "content",
      "summary_large_image",
    );
    await expect(page.locator('meta[name="twitter:image"]')).toHaveAttribute(
      "content",
      /brookside-social-preview\.webp$/,
    );
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
      "href",
      /^https:\/\//,
    );
  });

  test("canonical URLs are set per page and keep /proof-of-concept canonical", async ({
    page,
  }) => {
    const expectations: Array<[string, RegExp]> = [
      ["/start-here", /\/start-here$/],
      ["/guided-demo", /\/guided-demo$/],
      ["/proof-of-concept", /\/proof-of-concept$/],
      ["/projects", /\/projects$/],
    ];
    for (const [path, pattern] of expectations) {
      await page.goto(path);
      await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
        "href",
        pattern,
      );
    }
  });

  test("both Brookside images are served as WebP", async ({ request }) => {
    for (const path of [
      "/images/civil-engineer/brookside-project-thumbnail.webp",
      "/images/civil-engineer/brookside-social-preview.webp",
    ]) {
      const response = await request.get(path);
      expect(response.status()).toBe(200);
      expect(response.headers()["content-type"]).toContain("image/webp");
    }
  });
});
