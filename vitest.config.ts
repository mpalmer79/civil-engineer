import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

// Vitest config for the frontend unit tests. Tests run in jsdom and never make
// real network calls (fetch is mocked). The "@/" alias mirrors the tsconfig
// path mapping so imports resolve the same way as in the app.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [{ find: /^@\//, replacement: `${rootDir}/` }],
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    include: ["**/*.test.{ts,tsx}"],
    // e2e holds Playwright specs, which have their own runner.
    exclude: ["node_modules", ".next", "backend", "e2e"],
    coverage: {
      provider: "v8",
      include: ["app/**", "components/**", "lib/**"],
      exclude: [
        "**/*.test.*",
        "lib/api/generated/**",
        "lib/guide/generated/**",
        "app/api/session/register/route.ts",
      ],
      // Ratchet floors at the measured baseline so coverage can only rise.
      // Floors were re-baselined when the suite moved from vitest 2 to
      // vitest 4: the v8 coverage remapping changed how statements and
      // branches are counted (same tests, same source). Raise these floors
      // as coverage grows, never lower them. Long-term targets are tracked
      // in docs/TESTING.md.
      thresholds: {
        statements: 51,
        branches: 42,
        functions: 47,
        lines: 52,
      },
    },
  },
});
