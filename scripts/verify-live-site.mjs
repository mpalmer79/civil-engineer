#!/usr/bin/env node
// Production Foundations Sprint 10 live-site verification script.
//
// Performs lightweight, safe checks against a deployed (or local) Civil Engineer
// AI frontend and backend. It never requires, reads, or prints secrets, tokens,
// or credentials. It only checks public endpoints and configuration shape.
//
// Usage:
//   node scripts/verify-live-site.mjs --frontend <url> --backend <url>
//   LIVE_FRONTEND_URL=<url> BACKEND_URL=<url> node scripts/verify-live-site.mjs
//
// Output uses safe labels: ok, warning, unavailable, needs operator review.
// It is operational diagnostics only and makes no engineering determination.

function parseArgs(argv) {
  const args = { frontend: "", backend: "" };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--frontend") args.frontend = argv[(i += 1)] ?? "";
    else if (arg === "--backend") args.backend = argv[(i += 1)] ?? "";
  }
  return args;
}

const cli = parseArgs(process.argv.slice(2));
const FRONTEND_URL = (cli.frontend || process.env.LIVE_FRONTEND_URL || "").trim();
const BACKEND_URL = (cli.backend || process.env.BACKEND_URL || "").trim();

const results = [];
function record(check, status, message) {
  results.push({ check, status, message });
}

function stripTrailingSlash(url) {
  return url.replace(/\/+$/, "");
}

async function fetchSafe(url) {
  try {
    const res = await fetch(url, { redirect: "follow" });
    return { ok: res.ok, status: res.status };
  } catch {
    return { ok: false, status: 0 };
  }
}

async function main() {
  if (!FRONTEND_URL && !BACKEND_URL) {
    record(
      "input",
      "needs operator review",
      "Provide --frontend and/or --backend (or LIVE_FRONTEND_URL / BACKEND_URL).",
    );
  }

  // Backend origin must not include an /api or /api/v1 path.
  if (BACKEND_URL) {
    if (/\/api(\/v1)?\/?$/.test(BACKEND_URL)) {
      record(
        "backend url shape",
        "warning",
        "BACKEND_URL must be the backend origin only, with no /api/v1 path.",
      );
    } else {
      record("backend url shape", "ok", "Backend URL is an origin only.");
    }

    const base = stripTrailingSlash(BACKEND_URL);
    const health = await fetchSafe(`${base}/health`);
    record(
      "backend /health",
      health.ok ? "ok" : "unavailable",
      health.ok
        ? "Backend health responded."
        : `Backend health did not respond (status ${health.status}).`,
    );

    const readiness = await fetchSafe(`${base}/api/v1/readiness`);
    if (readiness.status === 0) {
      record(
        "backend /api/v1/readiness",
        "unavailable",
        "Readiness route did not respond.",
      );
    } else {
      record(
        "backend /api/v1/readiness",
        readiness.ok ? "ok" : "warning",
        readiness.ok
          ? "Readiness route responded."
          : `Readiness route returned status ${readiness.status}.`,
      );
    }
  }

  // Frontend homepage and key public demo routes should load. These are the
  // recruiter/evaluator entry points: Start Here, the Guided Demo, the Brookside
  // Meadows sample project, and the deployment status page.
  if (FRONTEND_URL) {
    const frontBase = stripTrailingSlash(FRONTEND_URL);
    const routes = [
      { path: "/", label: "frontend homepage" },
      { path: "/start-here", label: "frontend /start-here" },
      { path: "/guided-demo", label: "frontend /guided-demo" },
      {
        path: "/projects/proj_brookside_meadows",
        label: "frontend Brookside Meadows",
      },
      { path: "/deployment-status", label: "frontend /deployment-status" },
    ];
    for (const route of routes) {
      const res = await fetchSafe(frontBase + route.path);
      record(
        route.label,
        res.ok ? "ok" : "unavailable",
        res.ok
          ? `Route ${route.path} responded.`
          : `Route ${route.path} did not respond (status ${res.status}).`,
      );
    }
  }

  // Print a safe summary. No secrets, tokens, or credentials are ever printed.
  let worst = "ok";
  const rank = { ok: 0, warning: 1, "needs operator review": 2, unavailable: 3 };
  for (const r of results) {
    if ((rank[r.status] ?? 0) > (rank[worst] ?? 0)) worst = r.status;
    console.log(`[${r.status}] ${r.check}: ${r.message}`);
  }
  console.log(`\nOverall: ${worst}`);
  // Exit non-zero only when something is unavailable, so CI or an operator can
  // gate on it. Warnings and operator-review notices do not fail the run.
  process.exit(worst === "unavailable" ? 1 : 0);
}

main();
