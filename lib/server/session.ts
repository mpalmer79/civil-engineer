// Server-only session cookie helpers for the backend-for-frontend layer.
// The backend access token lives in an HttpOnly cookie that browser JavaScript
// cannot read. A companion non-HttpOnly indicator cookie carries no secret; it
// exists ONLY as a rendering optimization (skip requests that would certainly
// 401) and is never authorization truth. Validated session state comes from
// GET /api/session/status, and any backend 401 clears both cookies.

import type { NextResponse } from "next/server";

export const SESSION_COOKIE = "ce_session";
export const SESSION_INDICATOR_COOKIE = "ce_session_active";

// Bounds for the backend-reported token lifetime. The cookie max age is
// derived from the login/register response's expires_in_minutes, never from a
// constant that could drift from backend configuration.
const MIN_SESSION_MINUTES = 1;
const MAX_SESSION_MINUTES = 60 * 24 * 30; // 30 days; anything above is a config error.

// Converts the backend's expires_in_minutes to a cookie max age in seconds.
// Returns null for missing, nonnumeric, zero, negative, or unreasonable
// values so callers fail closed instead of minting an unbounded cookie.
export function sessionMaxAgeSeconds(expiresInMinutes: unknown): number | null {
  if (typeof expiresInMinutes !== "number" || !Number.isFinite(expiresInMinutes)) {
    return null;
  }
  if (
    expiresInMinutes < MIN_SESSION_MINUTES ||
    expiresInMinutes > MAX_SESSION_MINUTES
  ) {
    return null;
  }
  return Math.floor(expiresInMinutes * 60);
}

const isProduction = () => process.env.NODE_ENV === "production";

export function applySessionCookies(
  res: NextResponse,
  token: string,
  maxAgeSeconds: number,
): void {
  res.cookies.set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: isProduction(),
    sameSite: "lax",
    path: "/",
    maxAge: maxAgeSeconds,
  });
  res.cookies.set(SESSION_INDICATOR_COOKIE, "1", {
    httpOnly: false,
    secure: isProduction(),
    sameSite: "lax",
    path: "/",
    maxAge: maxAgeSeconds,
  });
}

export function clearSessionCookies(res: NextResponse): void {
  res.cookies.set(SESSION_COOKIE, "", {
    httpOnly: true,
    secure: isProduction(),
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  res.cookies.set(SESSION_INDICATOR_COOKIE, "", {
    httpOnly: false,
    secure: isProduction(),
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
}

// The trusted application origin for CSRF Origin validation. When set
// (recommended for any deployment behind a reverse proxy, where the Host
// header reflects proxy internals), the Origin header of a mutating request
// must match it exactly: scheme, host, and port. When unset, the Origin host
// must match the request's Host header, which is correct for direct
// deployments and local development.
function trustedOrigin(): string | null {
  const configured = process.env.TRUSTED_APP_ORIGIN ?? null;
  if (!configured) return null;
  try {
    const url = new URL(configured);
    return url.origin;
  } catch {
    // A malformed configuration must not silently disable the check.
    return "__invalid_trusted_origin__";
  }
}

// CSRF gate for cookie-authenticated mutating requests. Two independent
// checks must pass:
//   1. When an Origin header is present it must match the trusted application
//      origin (exact scheme, host, and port) or, when none is configured, the
//      request Host header.
//   2. The request must carry the custom x-csrf-protection header, which a
//      cross-site attacker cannot add without a CORS preflight that the
//      browser will refuse for a cross-origin call.
// See docs/adr/0003-secure-session-architecture.md and
// docs/security/BFF_PROXY_THREAT_MODEL.md.
export function csrfViolation(req: Request): string | null {
  const origin = req.headers.get("origin");
  if (origin) {
    let parsed: URL;
    try {
      parsed = new URL(origin);
    } catch {
      return "Malformed Origin header.";
    }
    const trusted = trustedOrigin();
    if (trusted) {
      if (parsed.origin !== trusted) {
        return "Cross-origin request rejected.";
      }
    } else {
      const host = req.headers.get("host");
      if (parsed.host !== host) {
        return "Cross-origin request rejected.";
      }
    }
  }
  if (req.headers.get("x-csrf-protection") !== "1") {
    return "Missing CSRF protection header.";
  }
  return null;
}

export const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

// Correlation identifiers. Accepts a client-supplied x-request-id when it is
// short and alphabet-safe; otherwise generates a UUID. Credentials never
// appear in correlation output.
const REQUEST_ID_PATTERN = /^[A-Za-z0-9._-]{1,64}$/;

export function correlationId(req: Request): string {
  const supplied = req.headers.get("x-request-id");
  if (supplied && REQUEST_ID_PATTERN.test(supplied)) return supplied;
  return crypto.randomUUID();
}
