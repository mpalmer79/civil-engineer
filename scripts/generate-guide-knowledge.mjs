#!/usr/bin/env node
// Generates objective repository facts for the Civil Engineer AI Guide from
// allowlisted sources: package.json dependency versions, the frontend route
// list, ADR titles, and key documentation locations. Curated knowledge
// entries carry the semantic explanations; this file carries only mechanical
// facts, so the guide can answer "which Next.js version" without prose that
// could drift.
//
// Output: lib/guide/generated/repo-facts.json (committed; CI regenerates and
// fails when stale via scripts/check-guide-knowledge.mjs).

import { execSync } from "node:child_process";
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

function listRoutes(dir, base = "") {
  const routes = [];
  for (const item of readdirSync(path.join(repoRoot, "app", dir), { withFileTypes: true })) {
    if (item.isDirectory()) {
      // Route groups (parenthesized) do not contribute URL segments.
      const segment = item.name.startsWith("(") ? "" : `/${item.name}`;
      routes.push(...listRoutes(path.join(dir, item.name), base + segment));
    } else if (item.name === "page.tsx") {
      routes.push(base === "" ? "/" : base);
    }
  }
  return routes;
}

const pkg = JSON.parse(readFileSync(path.join(repoRoot, "package.json"), "utf8"));

const adrDir = path.join(repoRoot, "docs/adr");
const adrs = readdirSync(adrDir)
  .filter((f) => f.endsWith(".md"))
  .map((f) => {
    const firstLine = readFileSync(path.join(adrDir, f), "utf8").split("\n")[0];
    return { file: `docs/adr/${f}`, title: firstLine.replace(/^#\s*/, "") };
  });

let commit = null;
try {
  commit = execSync("git rev-parse HEAD", { cwd: repoRoot, encoding: "utf8" }).trim();
} catch {
  // Not a git checkout (for example a deployment tarball); omit the commit.
}

const facts = {
  schemaVersion: 1,
  // The commit the snapshot was generated from; the guide presents this as a
  // build snapshot, never as a live-updated timestamp.
  commit,
  dependencies: {
    next: pkg.dependencies.next,
    react: pkg.dependencies.react,
    "react-dom": pkg.dependencies["react-dom"],
    typescript: pkg.devDependencies.typescript,
    tailwindcss: pkg.devDependencies.tailwindcss,
    vitest: pkg.devDependencies.vitest,
  },
  nodeEngine: pkg.engines?.node ?? null,
  scripts: Object.keys(pkg.scripts),
  routes: listRoutes("").sort(),
  adrs,
  keyDocuments: [
    "docs/README.md",
    "docs/ROUTE_ARCHITECTURE.md",
    "docs/real-vs-mocked.md",
    "docs/100_SCORE_TRANSFORMATION.md",
    "docs/security/BFF_PROXY_THREAT_MODEL.md",
    "docs/civil-engineer-ai-guide.md",
  ],
  openApiContract: "lib/api/generated/openapi.json",
};

mkdirSync(path.join(repoRoot, "lib/guide/generated"), { recursive: true });
writeFileSync(
  path.join(repoRoot, "lib/guide/generated/repo-facts.json"),
  `${JSON.stringify(facts, null, 2)}\n`,
);
console.log(`Generated guide facts: ${facts.routes.length} routes, ${facts.adrs.length} ADRs.`);
