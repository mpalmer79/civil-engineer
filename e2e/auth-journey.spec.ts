import { expect, test } from "@playwright/test";

// Authentication journey: registration (which establishes a session), the
// project workspace, the Brookside project, command center, reviewer queue,
// logout, protected-route behavior, and cookie handling. The account is
// created in the disposable e2e database and never touches developer data.

// Unique per invocation so reruns against a warm local backend never collide
// with an account from an earlier run.
const EMAIL = `e2e.reviewer.${Date.now()}@example.com`;
const PASSWORD = "e2e-strong-passphrase-1";

test.describe.configure({ mode: "serial" });

test.describe("authentication journey", () => {
  test("registration establishes an HttpOnly cookie session", async ({
    page,
    context,
  }) => {
    await page.goto("/register");
    await page.getByLabel("Display name").fill("E2E Reviewer");
    await page.getByLabel("Email").fill(EMAIL);
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: "Create account" }).click();
    await page.waitForURL("**/me", { timeout: 20000 });

    const cookies = await context.cookies();
    const session = cookies.find((cookie) => cookie.name === "ce_session");
    expect(session).toBeTruthy();
    expect(session?.httpOnly).toBe(true);

    // No backend token may reach browser-readable storage.
    const storage = await page.evaluate(() => ({
      local: Object.entries({ ...localStorage }),
      session: Object.entries({ ...sessionStorage }),
    }));
    const flat = JSON.stringify([...storage.local, ...storage.session]);
    expect(flat).not.toContain("Bearer");
    expect(flat).not.toMatch(/token/i);
  });

  test("login reaches the workspace and the Brookside project", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(EMAIL);
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("**/me", { timeout: 20000 });

    await page.goto("/projects/proj_brookside_meadows");
    await expect(page.locator("body")).toContainText("Brookside Meadows");

    await page.goto("/projects/proj_brookside_meadows/command-center");
    await expect(page.locator("h1, h2").first()).toBeVisible();

    await page.goto("/dashboard/queue");
    await expect(page.locator("body")).not.toContainText(
      "Something went wrong",
    );
  });

  test("logout clears the session cookies", async ({ page, context }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(EMAIL);
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("**/me", { timeout: 20000 });

    // Logout via the session endpoint the UI uses.
    const logout = await page.request.post("/api/session/logout", {
      headers: { "x-csrf-protection": "1" },
    });
    expect(logout.ok()).toBe(true);

    const cookies = await context.cookies();
    expect(
      cookies.find((cookie) => cookie.name === "ce_session")?.value ?? "",
    ).toBe("");

    // The session status endpoint reports unauthenticated, explicitly.
    const status = await page.request.get("/api/session/status");
    const body = await status.json();
    expect(body.authenticated).toBe(false);
  });
});
