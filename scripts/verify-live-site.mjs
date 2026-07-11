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

async function fetchText(url) {
  try {
    const res = await fetch(url, { redirect: "follow" });
    return { ok: res.ok, status: res.status, text: res.ok ? await res.text() : "" };
  } catch {
    return { ok: false, status: 0, text: "" };
  }
}

async function fetchHead(url) {
  try {
    const res = await fetch(url, { redirect: "follow" });
    const contentType = res.headers.get("content-type") ?? "";
    // Drain the body so connections are released promptly.
    await res.arrayBuffer();
    return { ok: res.ok, status: res.status, contentType };
  } catch {
    return { ok: false, status: 0, contentType: "" };
  }
}

async function fetchRedirect(url) {
  try {
    const res = await fetch(url, { redirect: "manual" });
    return { status: res.status, location: res.headers.get("location") ?? "" };
  } catch {
    return { status: 0, location: "" };
  }
}

// Pulls a meta tag's content attribute out of rendered HTML, tolerating
// either attribute order.
function metaContent(html, key, value) {
  const patterns = [
    new RegExp(`<meta[^>]*${key}="${value}"[^>]*content="([^"]*)"`, "i"),
    new RegExp(`<meta[^>]*content="([^"]*)"[^>]*${key}="${value}"`, "i"),
  ];
  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match) return match[1];
  }
  return null;
}

function canonicalHref(html) {
  const match =
    html.match(/<link[^>]*rel="canonical"[^>]*href="([^"]*)"/i) ??
    html.match(/<link[^>]*href="([^"]*)"[^>]*rel="canonical"/i);
  return match ? match[1] : null;
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
      { path: "/proof-of-concept", label: "frontend /proof-of-concept" },
      { path: "/projects", label: "frontend /projects" },
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

    // Short proof aliases must permanently redirect to the canonical
    // /proof-of-concept route.
    for (const alias of ["/poc", "/proofofconcept"]) {
      const redirect = await fetchRedirect(frontBase + alias);
      const redirected =
        redirect.status >= 301 &&
        redirect.status <= 308 &&
        redirect.location.includes("/proof-of-concept");
      record(
        `redirect ${alias}`,
        redirected ? "ok" : "mismatch",
        redirected
          ? `${alias} redirects to /proof-of-concept (status ${redirect.status}).`
          : `${alias} did not redirect to /proof-of-concept (status ${redirect.status}, location "${redirect.location}").`,
      );
    }

    // Brookside media assets must be served as WebP.
    const mediaAssets = [
      {
        path: "/images/civil-engineer/brookside-project-thumbnail.webp",
        label: "brookside original image",
      },
      {
        path: "/images/civil-engineer/brookside-social-preview.webp",
        label: "brookside social preview",
      },
    ];
    for (const asset of mediaAssets) {
      const res = await fetchHead(frontBase + asset.path);
      const good = res.status === 200 && res.contentType.includes("image/webp");
      record(
        asset.label,
        good ? "ok" : "mismatch",
        good
          ? `${asset.path} returned 200 image/webp.`
          : `${asset.path} returned status ${res.status} with content-type "${res.contentType}".`,
      );
    }

    // Homepage social metadata: absolute HTTPS og:image pointing at the
    // Brookside social preview, declared 1200x630, summary_large_image card.
    const home = await fetchText(`${frontBase}/`);
    if (!home.ok) {
      record("homepage metadata", "unavailable", "Homepage HTML could not be fetched.");
    } else {
      const ogImage = metaContent(home.text, "property", "og:image") ?? "";
      const ogImageOk =
        ogImage.startsWith("https://") &&
        ogImage.includes("brookside-social-preview.webp");
      record(
        "homepage og:image",
        ogImageOk ? "ok" : "mismatch",
        ogImageOk
          ? "og:image is an absolute HTTPS URL for brookside-social-preview.webp."
          : `og:image is "${ogImage}".`,
      );
      const ogWidth = metaContent(home.text, "property", "og:image:width");
      const ogHeight = metaContent(home.text, "property", "og:image:height");
      const dimsOk = ogWidth === "1200" && ogHeight === "630";
      record(
        "homepage og:image dimensions",
        dimsOk ? "ok" : "mismatch",
        dimsOk
          ? "og:image declares 1200x630."
          : `og:image declares ${ogWidth}x${ogHeight}.`,
      );
      const ogAlt = metaContent(home.text, "property", "og:image:alt") ?? "";
      record(
        "homepage og:image:alt",
        ogAlt.length > 0 ? "ok" : "mismatch",
        ogAlt.length > 0 ? "og:image:alt is present." : "og:image:alt is missing.",
      );
      const twitterCard = metaContent(home.text, "name", "twitter:card");
      record(
        "homepage twitter:card",
        twitterCard === "summary_large_image" ? "ok" : "mismatch",
        `twitter:card is "${twitterCard}".`,
      );
      const twitterImage = metaContent(home.text, "name", "twitter:image") ?? "";
      const twitterImageOk = twitterImage.includes("brookside-social-preview.webp");
      record(
        "homepage twitter:image",
        twitterImageOk ? "ok" : "mismatch",
        twitterImageOk
          ? "twitter:image points at the Brookside social preview."
          : `twitter:image is "${twitterImage}".`,
      );
    }

    // Canonical URLs. /proof-of-concept is the canonical proof URL; the /poc
    // and /proofofconcept aliases redirect and never appear as canonicals.
    const canonicalExpectations = [
      { path: "/", suffix: "/" },
      { path: "/start-here", suffix: "/start-here" },
      { path: "/guided-demo", suffix: "/guided-demo" },
      { path: "/proof-of-concept", suffix: "/proof-of-concept" },
      { path: "/projects", suffix: "/projects" },
    ];
    for (const expectation of canonicalExpectations) {
      const res = await fetchText(frontBase + expectation.path);
      if (!res.ok) {
        record(
          `canonical ${expectation.path}`,
          "unavailable",
          `Route ${expectation.path} could not be fetched for canonical check.`,
        );
        continue;
      }
      const href = canonicalHref(res.text) ?? "";
      const canonicalOk =
        href.startsWith("https://") &&
        (expectation.suffix === "/"
          ? /^https:\/\/[^/]+\/?$/.test(href)
          : stripTrailingSlash(href).endsWith(expectation.suffix));
      record(
        `canonical ${expectation.path}`,
        canonicalOk ? "ok" : "mismatch",
        canonicalOk
          ? `Canonical is "${href}".`
          : `Canonical is "${href}", expected an absolute URL ending in "${expectation.suffix}".`,
      );
    }

    // Brookside visual placements and their required disclosures.
    const contentExpectations = [
      {
        path: "/start-here",
        label: "start-here brookside visual",
        needles: [
          "brookside-project-thumbnail.webp",
          "Synthetic case-study visualization. Not a real project, survey, approved design, or constructed development.",
        ],
      },
      {
        path: "/proof-of-concept",
        label: "proof-of-concept brookside visual",
        needles: [
          "brookside-project-thumbnail.webp",
          "The downloadable DXF is a separately generated test drawing used to exercise the real upload and parsing pipeline.",
        ],
      },
      {
        path: "/guided-demo",
        label: "guided-demo brookside cover",
        needles: [
          "Brookside Meadows Guided Review",
          "brookside-project-thumbnail.webp",
          "Synthetic case-study visualization. Not a real project, survey, approved design, or constructed development.",
        ],
      },
    ];
    for (const expectation of contentExpectations) {
      const res = await fetchText(frontBase + expectation.path);
      if (!res.ok) {
        record(
          expectation.label,
          "unavailable",
          `Route ${expectation.path} could not be fetched for content check.`,
        );
        continue;
      }
      const missing = expectation.needles.filter(
        (needle) => !res.text.includes(needle),
      );
      record(
        expectation.label,
        missing.length === 0 ? "ok" : "mismatch",
        missing.length === 0
          ? `${expectation.path} shows the Brookside visual and required wording.`
          : `${expectation.path} is missing: ${missing.join(" | ")}`,
      );
    }
  }

  // Print a safe summary. No secrets, tokens, or credentials are ever printed.
  let worst = "ok";
  const rank = {
    ok: 0,
    warning: 1,
    "needs operator review": 2,
    mismatch: 3,
    unavailable: 3,
  };
  for (const r of results) {
    if ((rank[r.status] ?? 0) > (rank[worst] ?? 0)) worst = r.status;
    console.log(`[${r.status}] ${r.check}: ${r.message}`);
  }
  console.log(`\nOverall: ${worst}`);
  // Exit non-zero when something is unavailable or does not match its
  // expected state, so CI or an operator can gate on it. Warnings and
  // operator-review notices do not fail the run.
  process.exit(worst === "unavailable" || worst === "mismatch" ? 1 : 0);
}

main();
