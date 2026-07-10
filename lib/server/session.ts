// Server-only session cookie helpers for the backend-for-frontend layer.
// The backend access token lives in an HttpOnly cookie that browser JavaScript
// cannot read. A companion non-HttpOnly indicator cookie carries no secret and
// lets the client skip requests that would certainly return 401.

import type { NextResponse } from "next/server";

export const SESSION_COOKIE = "ce_session";
export const SESSION_INDICATOR_COOKIE = "ce_session_active";

// Matches the backend token lifetime (AUTH_TOKEN_EXPIRE_MINUTES, 120 by
// default) so the cookie and the token it carries expire together. A cookie
// that outlives its token would send an expired credential and produce a
// confusing 401 while the UI still shows a session.
export const SESSION_MAX_AGE_SECONDS = 60 * 120;

const isProduction = () => process.env.NODE_ENV === "production";

export function applySessionCookies(res: NextResponse, token: string): void {
  res.cookies.set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: isProduction(),
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  });
  res.cookies.set(SESSION_INDICATOR_COOKIE, "1", {
    httpOnly: false,
    secure: isProduction(),
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
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

// CSRF gate for cookie-authenticated mutating requests. Two independent
// checks must pass:
//   1. When an Origin header is present it must match the request host
//      (browsers always send Origin on cross-site requests).
//   2. The request must carry the custom x-csrf-protection header, which a
//      cross-site attacker cannot add without a CORS preflight that the
//      browser will refuse for a cross-origin call.
// See docs/adr/0003-secure-session-architecture.md.
export function csrfViolation(req: Request): string | null {
  const origin = req.headers.get("origin");
  if (origin) {
    const host = req.headers.get("host");
    try {
      if (new URL(origin).host !== host) {
        return "Cross-origin request rejected.";
      }
    } catch {
      return "Malformed Origin header.";
    }
  }
  if (req.headers.get("x-csrf-protection") !== "1") {
    return "Missing CSRF protection header.";
  }
  return null;
}

export const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
