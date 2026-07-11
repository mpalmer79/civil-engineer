#!/usr/bin/env node
// Freshness and integrity gate for the Civil Engineer AI Guide knowledge.
// Fails when:
//   1. A repository path referenced by a knowledge entry, route-context entry,
//      or generated fact no longer exists.
//   2. An internal route link no longer resolves to a page (or documented
//      redirect).
//   3. The generated repo-facts.json is stale (dependency versions or route
//      list differ from the repository).
//   4. A knowledge claim contradicts an enforced repository fact (the stale
//      seeded-fallback claim is explicitly guarded).
//
// Runs in CI and through `npm run check:guide`.

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const failures = [];

// Load the knowledge catalog and route context through the compiled TS via a
// lightweight extraction: run vitest? No; parse with a TS loader is heavy.
// The catalog is plain data, so import it through a tsx-free trick: transpile
// on the fly with the TypeScript compiler API would add a dependency. Instead,
// extract string literals from the source files for the checks that matter.

function extractField(source, field) {
  // Collects every string inside `field: [ ... ]` arrays across the file.
  const results = [];
  const arrayPattern = new RegExp(`${field}:\\s*\\[([^\\]]*)\\]`, "g");
  for (const match of source.matchAll(arrayPattern)) {
    for (const str of match[1].matchAll(/"([^"]+)"/g)) results.push(str[1]);
  }
  return results;
}

const knowledgeSource = readFileSync(path.join(repoRoot, "lib/guide/knowledge.ts"), "utf8");
const routeContextSource = readFileSync(path.join(repoRoot, "lib/guide/routeContext.ts"), "utf8");

// 1. Repository paths must exist.
const referencedPaths = [
  ...extractField(knowledgeSource, "sources"),
  ...extractField(knowledgeSource, "implementation"),
  ...extractField(knowledgeSource, "tests"),
  ...extractField(routeContextSource, "sources"),
];
for (const p of new Set(referencedPaths)) {
  if (!existsSync(path.join(repoRoot, p))) {
    failures.push(`Missing repository path referenced by guide knowledge: ${p}`);
  }
}

// 2. Internal route links must resolve to an app page.
const hrefs = new Set();
for (const match of knowledgeSource.matchAll(/href: "(\/[^"]*)"/g)) hrefs.add(match[1]);
for (const match of routeContextSource.matchAll(/href: "(\/[^"]*)"/g)) hrefs.add(match[1]);

function routeExists(href) {
  const clean = href.split("#")[0].split("?")[0];
  if (clean === "/") return existsSync(path.join(repoRoot, "app/page.tsx"));
  const segments = clean.split("/").filter(Boolean);
  // Walk the app directory allowing dynamic segments and route groups.
  function walk(dir, index) {
    if (index === segments.length) {
      if (existsSync(path.join(dir, "page.tsx"))) return true;
      // Route groups can hold the page one level deeper.
      try {
        for (const entry of require("node:fs").readdirSync(dir, { withFileTypes: true })) {
          if (entry.isDirectory() && entry.name.startsWith("(")) {
            if (walk(path.join(dir, entry.name), index)) return true;
          }
        }
      } catch {
        return false;
      }
      return false;
    }
    const seg = segments[index];
    const { readdirSync } = require("node:fs");
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return false;
    }
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (entry.name.startsWith("(")) {
        if (walk(path.join(dir, entry.name), index)) return true;
      } else if (entry.name === seg || (entry.name.startsWith("[") && entry.name.endsWith("]"))) {
        if (walk(path.join(dir, entry.name), index + 1)) return true;
      }
    }
    return false;
  }
  return walk(path.join(repoRoot, "app"), 0);
}

import { createRequire } from "node:module";
const require = createRequire(import.meta.url);

for (const href of hrefs) {
  if (!routeExists(href)) {
    failures.push(`Guide links to a route that does not resolve: ${href}`);
  }
}

// 3. Generated facts must be current.
const factsPath = path.join(repoRoot, "lib/guide/generated/repo-facts.json");
if (!existsSync(factsPath)) {
  failures.push("lib/guide/generated/repo-facts.json is missing. Run: npm run generate:guide");
} else {
  const before = readFileSync(factsPath, "utf8");
  execFileSync("node", ["scripts/generate-guide-knowledge.mjs"], { cwd: repoRoot, stdio: "ignore" });
  const after = readFileSync(factsPath, "utf8");
  // The commit field changes every commit; compare everything else.
  const stripCommit = (s) => s.replace(/"commit": "[^"]*"/, '"commit": null');
  if (stripCommit(before) !== stripCommit(after)) {
    failures.push("Generated guide facts are stale. Run: npm run generate:guide and commit the result.");
  }
}

// 4. Contradiction guards: claims the repository has retired must not appear.
const forbiddenClaims = [
  { text: "falls back to seeded demo data when the backend is unreachable", reason: "authenticated surfaces render explicit failure states; only public demo surfaces show labeled fixtures" },
  { text: "falls back to seeded data", reason: "same" },
];
for (const claim of forbiddenClaims) {
  if (knowledgeSource.includes(claim.text)) {
    failures.push(`Stale claim in guide knowledge: "${claim.text}" (${claim.reason})`);
  }
}

if (failures.length > 0) {
  console.error("Guide knowledge check failed:");
  for (const f of failures) console.error(`  ${f}`);
  process.exit(1);
}
console.log("Guide knowledge check passed.");
