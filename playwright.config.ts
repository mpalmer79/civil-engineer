import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { defineConfig } from "@playwright/test";

// Browser release suite. Runs the production Next.js server against a real
// FastAPI backend seeded with the synthetic Brookside Meadows fixture in a
// disposable SQLite database, so no developer data is ever touched and no
// external service is required.
//
// Run locally with: npm run build && npx playwright test
// CI runs the same sequence in the e2e job.

const FRONTEND_PORT = 3000;
const BACKEND_PORT = 8000;
const FRONTEND_ORIGIN = `http://127.0.0.1:${FRONTEND_PORT}`;
const BACKEND_ORIGIN = `http://127.0.0.1:${BACKEND_PORT}`;

// Disposable per-run backend state. os.tmpdir keeps it out of the repository.
const RUN_DIR = path.join(
  os.tmpdir(),
  `civil-engineer-e2e-${process.env.TEST_WORKER_INDEX ?? "run"}`,
);
fs.mkdirSync(path.join(RUN_DIR, "cad-uploads"), { recursive: true });
// A fresh database per invocation so reruns never see stale accounts.
fs.rmSync(path.join(RUN_DIR, "e2e.db"), { force: true });

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["github"]] : [["list"]],
  timeout: 60_000,
  use: {
    baseURL: FRONTEND_ORIGIN,
    trace: "retain-on-failure",
    // Some sandboxes pre-install Chromium at a fixed path instead of the
    // Playwright cache. Use it when present; CI installs the matching
    // browser build and takes the default path.
    ...(process.env.CI
      ? {}
      : fs.existsSync("/opt/pw-browsers/chromium")
        ? { launchOptions: { executablePath: "/opt/pw-browsers/chromium" } }
        : {}),
  },
  webServer: [
    {
      command:
        "python3 -m uvicorn app.main:app --host 127.0.0.1 --port " +
        `${BACKEND_PORT}`,
      cwd: "./backend",
      url: `${BACKEND_ORIGIN}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        DATABASE_URL: `sqlite:///${path.join(RUN_DIR, "e2e.db")}`,
        CAD_UPLOAD_DIR: path.join(RUN_DIR, "cad-uploads"),
        AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS: "false",
        AUTH_DEMO_MODE: "true",
        AUTH_ALLOW_PUBLIC_DEMO: "true",
        AUTH_SECRET_KEY: "e2e-test-secret-key",
      },
    },
    {
      command: `npm run start -- --hostname 127.0.0.1 --port ${FRONTEND_PORT}`,
      url: FRONTEND_ORIGIN,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        BACKEND_API_BASE_URL: BACKEND_ORIGIN,
        NEXT_PUBLIC_API_BASE_URL: BACKEND_ORIGIN,
        TRUSTED_APP_ORIGIN: FRONTEND_ORIGIN,
      },
    },
  ],
});
