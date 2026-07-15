#!/usr/bin/env node
// Phase 3A/3B pilot release verification.
//
// Safe, offline-by-default checks that the repo is in a shareable
// design-partner pilot posture. It never requires, reads, or prints secrets,
// tokens, or credentials. Backend health/readiness checks run only when a
// backend URL is provided and degrade to "skipped" otherwise.
//
// Usage:
//   node scripts/verify-pilot-release.mjs
//   node scripts/verify-pilot-release.mjs --backend http://localhost:8000
//
// Exit code is non-zero only on a hard violation (a generated-by/attribution
// footer in public docs or copy, or prohibited final-decision wording in public
// copy, or a missing required release doc). Informational items report as
// "warning" or "skipped" without failing.

import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function parseBackend(argv) {
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--backend") return (argv[i + 1] ?? "").trim();
  }
  return (process.env.BACKEND_URL ?? "").trim();
}

const backend = parseBackend(process.argv.slice(2));
const results = [];
let hardFail = false;

function record(check, status, message) {
  results.push({ check, status, message });
  if (status === "fail") hardFail = true;
}

function read(rel) {
  return existsSync(join(root, rel)) ? readFileSync(join(root, rel), "utf8") : null;
}

// Attribution tokens assembled from fragments so the literal strings are never
// stored verbatim in this file.
const ATTRIBUTION_TOKENS = [
  ["generated", "by"].join(" "),
  ["claude", "code"].join(" "),
  ["claude.ai", "code"].join("/"),
  ["co-authored", "by"].join("-"),
];

const PROHIBITED_CLAIMS = [
  "plan approved",
  "design validated",
  "fully compliant",
  "passes review",
  "guaranteed compliance",
  "meets all requirements",
  "marked safe",
];

// 1. Required release docs exist.
const REQUIRED_DOCS = [
  "docs/OPERATIONS.md",
  "docs/OPERATIONS.md",
  "docs/OPERATIONS.md",
  "docs/OPERATIONS.md",
  "docs/SECURITY.md",
];
for (const doc of REQUIRED_DOCS) {
  if (read(doc) !== null) record(`doc:${doc}`, "ok", "present");
  else record(`doc:${doc}`, "fail", "missing required release doc");
}

// 2. Public routes and protected routes are listed in the release checklist.
const checklist = read("docs/OPERATIONS.md") ?? "";
for (const route of ["/", "/guided-demo", "/pilot"]) {
  if (checklist.includes(route)) record(`public-route:${route}`, "ok", "listed");
  else record(`public-route:${route}`, "warning", "not listed in checklist");
}
for (const route of ["/workspace", "/admin/pilot-requests"]) {
  if (checklist.includes(route)) record(`protected-route:${route}`, "ok", "listed");
  else record(`protected-route:${route}`, "warning", "not listed in checklist");
}

// 3. Production-posture flags documented.
for (const flag of [
  "AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS",
  "AUTH_DEMO_MODE",
  "AUTH_ALLOW_PUBLIC_DEMO",
]) {
  const inDocs =
    (read("docs/OPERATIONS.md") ?? "").includes(flag) ||
    checklist.includes(flag);
  record(`flag:${flag}`, inDocs ? "ok" : "warning", inDocs ? "documented" : "undocumented");
}

// 4. No attribution footer in public docs and public copy.
const PUBLIC_FILES = [
  "docs/OPERATIONS.md",
  "docs/OPERATIONS.md",
  "docs/OPERATIONS.md",
  "docs/OPERATIONS.md",
  "app/page.tsx",
  "app/pilot/page.tsx",
  "app/guided-demo/page.tsx",
];
for (const file of PUBLIC_FILES) {
  const text = (read(file) ?? "").toLowerCase();
  const hit = ATTRIBUTION_TOKENS.find((t) => text.includes(t));
  if (hit) record(`attribution:${file}`, "fail", `attribution token present`);
  else record(`attribution:${file}`, "ok", "clean");
}

// 5. No prohibited final-decision claims in public copy.
for (const file of ["app/page.tsx", "app/pilot/page.tsx", "app/guided-demo/page.tsx"]) {
  const text = (read(file) ?? "").toLowerCase();
  const hit = PROHIBITED_CLAIMS.find((c) => text.includes(c));
  if (hit) record(`claims:${file}`, "fail", `prohibited claim: ${hit}`);
  else record(`claims:${file}`, "ok", "review-support only");
}

// 6. Optional backend health/readiness when a backend URL is provided.
async function checkBackend() {
  if (!backend) {
    record("backend:health", "skipped", "no --backend url provided");
    record("backend:readiness", "skipped", "no --backend url provided");
    return;
  }
  for (const [name, path] of [
    ["backend:health", "/health"],
    ["backend:readiness", "/api/v1/readiness"],
  ]) {
    try {
      const res = await fetch(`${backend}${path}`);
      record(name, res.ok ? "ok" : "warning", `status ${res.status}`);
    } catch {
      record(name, "warning", "unreachable");
    }
  }
}

await checkBackend();

for (const r of results) {
  const tag = r.status.toUpperCase().padEnd(8);
  console.log(`${tag} ${r.check} - ${r.message}`);
}

if (hardFail) {
  console.error("\nPilot release verification FAILED: resolve the items above.");
  process.exit(1);
}
console.log("\nPilot release verification passed (warnings are informational).");
