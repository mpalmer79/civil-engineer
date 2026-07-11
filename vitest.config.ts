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
      // The documented targets (70 statements/lines, 65 branches, 60
      // functions) are tracked in docs/100_SCORE_TRANSFORMATION.md and not
      // yet met; raise these floors as coverage grows, never lower them.
      thresholds: {
        statements: 57,
        branches: 62,
        functions: 50,
        lines: 57,
      },
    },
  },
});
