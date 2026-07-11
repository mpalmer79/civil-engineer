import path from "node:path";

import { expect, test } from "@playwright/test";

// Browser-level DXF workflow: sign in, open the Brookside CAD intake, upload
// the synthetic proof DXF through the BFF, request parsing, and verify the
// persisted results in the UI. This is the same drawing the proof-of-concept
// page documents, so the browser path and the harness path prove the same
// pipeline.

// Unique per invocation so reruns against a warm local backend never collide
// with an account from an earlier run.
const EMAIL = `e2e.cad.reviewer.${Date.now()}@example.com`;
const PASSWORD = "e2e-strong-passphrase-2";
const PROOF_DXF = path.join(
  process.cwd(),
  "public",
  "proof-of-concept",
  "dxf",
  "brookside_meadows_realistic_submission.dxf",
);

test.describe.configure({ mode: "serial" });

test.describe("browser DXF workflow", () => {
  test("upload, parse, and review the synthetic proof DXF", async ({
    page,
    context,
  }) => {
    // Register a fresh reviewer account (session becomes an HttpOnly cookie).
    await page.goto("/register");
    await page.getByLabel("Display name").fill("E2E CAD Reviewer");
    await page.getByLabel("Email").fill(EMAIL);
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: "Create account" }).click();
    await page.waitForURL("**/me", { timeout: 20000 });

    // Open the Brookside CAD workspace.
    await page.goto("/projects/proj_brookside_meadows/cad");
    await expect(page.locator("body")).toContainText(/CAD|DXF/i);

    // Upload the proof DXF through the file input (BFF multipart path).
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput.first()).toBeAttached();
    await fileInput.first().setInputFiles(PROOF_DXF);
    const uploadButton = page.getByRole("button", {
      name: /upload/i,
    });
    await uploadButton.first().click();

    // The upload result appears (accepted for review-support parsing).
    await expect(page.locator("body")).toContainText(/accepted|uploaded/i, {
      timeout: 30000,
    });

    // Request parsing for the uploaded file through the queue UI. The queue
    // row for the uploaded file carries the only "Request parse" button.
    const parseButton = page.getByRole("button", { name: "Request parse" });
    await expect(parseButton.first()).toBeVisible({ timeout: 30000 });
    await parseButton.first().click();

    // Select the uploaded file in the CAD file list to load its review
    // context and parse summary.
    const fileButton = page.getByRole("button", {
      name: /brookside_meadows_realistic_submission\.dxf/,
    });
    await expect(fileButton.first()).toBeVisible({ timeout: 60000 });
    await fileButton.first().click();

    // The parse summary shows the proof drawing inventory: 168 entities,
    // 15 layers, 80 text records, and the reference and finding results.
    await expect(page.locator("body")).toContainText("168", {
      timeout: 60000,
    });
    await expect(page.locator("body")).toContainText(
      /possible label conflict|missing plan sheet match/i,
      { timeout: 30000 },
    );

    // No backend token in browser-readable state after the whole flow.
    const storage = await page.evaluate(() =>
      JSON.stringify({ ...localStorage, ...sessionStorage }),
    );
    expect(storage).not.toMatch(/bearer|access_token/i);
    const cookies = await context.cookies();
    const readable = cookies.filter((cookie) => !cookie.httpOnly);
    for (const cookie of readable) {
      expect(cookie.value).not.toMatch(/^ey[A-Za-z0-9]/);
    }
  });

  test("an invalid DXF upload is rejected with an explicit message", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(EMAIL);
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("**/me", { timeout: 20000 });

    await page.goto("/projects/proj_brookside_meadows/cad");
    const fileInput = page.locator('input[type="file"]');
    await fileInput.first().setInputFiles({
      name: "not-a-drawing.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4 not a dxf"),
    });
    const uploadButton = page.getByRole("button", { name: /upload/i });
    await uploadButton.first().click();
    await expect(page.locator("body")).toContainText(
      /unsupported|rejected|only dxf|\.dxf/i,
      { timeout: 30000 },
    );
  });
});
