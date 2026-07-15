#!/usr/bin/env node
// Repository complexity budget. Reports authored source files that exceed
// the agreed size heuristics and fails the build when a file crosses the
// hard ceiling without an allowlist entry.
//
// Policy (docs/adr/0007-repository-consolidation.md):
//   TypeScript / TSX   warn at 300 lines, fail at 500
//   Python             warn at 400 lines, fail at 700
// Generated files, migrations, and deliberately approved data fixtures are
// exempt. The allowlist below must stay small; every entry needs a reason.
//
// Usage: node scripts/check-complexity.mjs [--verbose]

import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

const verbose = process.argv.includes("--verbose");

const BUDGETS = [
  { exts: [".ts", ".tsx"], warn: 300, fail: 500 },
  { exts: [".py"], warn: 400, fail: 700 },
];

// Paths exempt from the budget entirely.
const EXEMPT_PREFIXES = [
  "lib/api/generated/", // generated OpenAPI contract
  "lib/guide/generated/", // generated guide facts
  "backend/app/migrations/versions/", // schema history, append only
  "node_modules/",
  ".next/",
];

// Files allowed to exceed the failure ceiling because they are cohesive by
// nature: linear scripts or curated data catalogs that a split would only
// fragment. Keep this list short; every entry needs a one-line reason.
const COHESION_ALLOWLIST = new Map([
  // Deterministic proof harness: a single linear script whose steps mirror
  // the published validation report; splitting it would obscure the audit
  // trail between script sections and report sections.
  ["scripts/run_dxf_proof.py", "single linear deterministic proof harness"],
  // Seeded reference-project fixtures: cohesive data modules, reviewed as
  // data rather than logic.
  ["backend/app/db/seeds/plan_sheets.py", "reference-project data fixture"],
  ["backend/app/db/seeds/evidence.py", "reference-project data fixture"],
  ["backend/app/db/seeds/reference_project.py", "reference-project data fixture"],
  // Curated, allowlisted guide catalog: reviewed as a data catalog, not
  // logic; source paths are independently validated by check-guide-knowledge.
  ["lib/guide/knowledge.ts", "curated guide knowledge catalog (data, not logic)"],
]);

// Modules that still exceed the ceiling and are scheduled for decomposition
// in a tracked follow-up. This registry is deliberately visible so the
// backlog cannot hide: it is enumerated in
// docs/internal/REFACTOR_VALIDATION_REPORT.md with the target sequence.
// Entries must only shrink. Do not add new files here to dodge the ceiling;
// new oversized files must be split before merge.
const DEFERRED_SPLIT = new Map([
  ["app/__tests__/evidenceRetrieval.test.tsx", "deferred: split by behavior (search, ranking, filters, citations)"],
]);

const ALLOWLIST = new Map([...COHESION_ALLOWLIST, ...DEFERRED_SPLIT]);

const files = execFileSync("git", ["ls-files"], { encoding: "utf8" })
  .split("\n")
  .filter(Boolean);

const failures = [];
const warnings = [];

for (const file of files) {
  if (EXEMPT_PREFIXES.some((p) => file.startsWith(p))) continue;
  const budget = BUDGETS.find((b) => b.exts.some((e) => file.endsWith(e)));
  if (!budget) continue;

  let lines;
  try {
    lines = readFileSync(file, "utf8").split("\n").length;
  } catch {
    continue;
  }

  if (lines > budget.fail) {
    if (ALLOWLIST.has(file)) {
      if (verbose) {
        console.log(`allowlisted ${file} (${lines} lines): ${ALLOWLIST.get(file)}`);
      }
      continue;
    }
    failures.push({ file, lines, limit: budget.fail });
  } else if (lines > budget.warn) {
    warnings.push({ file, lines, limit: budget.warn });
  }
}

for (const [file] of ALLOWLIST) {
  if (!files.includes(file)) {
    failures.push({ file, lines: 0, limit: 0, stale: true });
  }
}

warnings.sort((a, b) => b.lines - a.lines);
failures.sort((a, b) => b.lines - a.lines);

if (warnings.length > 0) {
  console.log(`Complexity warnings (${warnings.length} files over the soft budget):`);
  for (const w of warnings) {
    console.log(`  warn  ${w.file}: ${w.lines} lines (soft budget ${w.limit})`);
  }
}

if (failures.length > 0) {
  console.error(`\nComplexity failures (${failures.length}):`);
  for (const f of failures) {
    if (f.stale) {
      console.error(`  fail  stale allowlist entry, file no longer exists: ${f.file}`);
    } else {
      console.error(
        `  fail  ${f.file}: ${f.lines} lines exceeds the hard ceiling of ${f.limit}. ` +
          "Split the module by responsibility or, with a strong cohesion argument, " +
          "add an allowlist entry with a reason in scripts/check-complexity.mjs.",
      );
    }
  }
  process.exit(1);
}

console.log(
  warnings.length === 0
    ? "Complexity budget: all authored files within budget."
    : "Complexity budget: no hard failures.",
);
