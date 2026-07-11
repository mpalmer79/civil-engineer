#!/usr/bin/env node
// Regenerates the frontend wire contract from the FastAPI OpenAPI schema.
//
//   1. backend/.venv (or the active python) exports app.openapi() to
//      lib/api/generated/openapi.json (sorted keys, stable output).
//   2. openapi-typescript converts it to lib/api/generated/schema.d.ts.
//
// Both artifacts are committed. CI regenerates them and fails when the
// committed output is stale (see .github/workflows/ci.yml). Generated files
// must never be edited by hand.
//
// Usage: node scripts/generate-api-types.mjs [--check]
//   --check  regenerate to a temp location and fail if committed files differ.

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const check = process.argv.includes("--check");

const python = ["backend/.venv/bin/python", "python3", "python"]
  .map((p) => (p.startsWith("backend/") ? path.join(repoRoot, p) : p))
  .find((p) => {
    try {
      execFileSync(p, ["--version"], { stdio: "ignore" });
      return true;
    } catch {
      return false;
    }
  });

if (!python) {
  console.error("No usable Python interpreter found.");
  process.exit(1);
}

const exportScript = `
import json, sys
sys.path.insert(0, "backend")
from app.main import app
schema = app.openapi()
with open("lib/api/generated/openapi.json", "w") as f:
    json.dump(schema, f, indent=2, sort_keys=True)
    f.write("\\n")
`;

function run(cmd, args, opts = {}) {
  execFileSync(cmd, args, { cwd: repoRoot, stdio: "inherit", ...opts });
}

const before = {
  json: readFileSync(path.join(repoRoot, "lib/api/generated/openapi.json"), "utf8"),
  dts: existsSync(path.join(repoRoot, "lib/api/generated/schema.d.ts"))
    ? readFileSync(path.join(repoRoot, "lib/api/generated/schema.d.ts"), "utf8")
    : "",
};

run(python, ["-c", exportScript]);
run("npx", ["openapi-typescript", "lib/api/generated/openapi.json", "-o", "lib/api/generated/schema.d.ts"]);

if (check) {
  const after = {
    json: readFileSync(path.join(repoRoot, "lib/api/generated/openapi.json"), "utf8"),
    dts: readFileSync(path.join(repoRoot, "lib/api/generated/schema.d.ts"), "utf8"),
  };
  if (after.json !== before.json || after.dts !== before.dts) {
    console.error(
      "Generated API contract is stale. Run: node scripts/generate-api-types.mjs and commit the result.",
    );
    process.exit(1);
  }
  console.log("Generated API contract is current.");
}
