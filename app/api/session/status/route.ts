// Session status endpoint: the authoritative, validated view of the browser
// session. It reads the HttpOnly cookie server-side, validates the token
// against the backend, returns only non-sensitive session state, and clears
// invalid cookies. The client-readable indicator cookie is only a rendering
// optimization; this endpoint is the truth the application shell relies on.

import { NextRequest, NextResponse } from "next/server";

import { BACKEND_ORIGIN } from "@/lib/api/client";
import {
  SESSION_COOKIE,
  clearSessionCookies,
  correlationId,
} from "@/lib/server/session";

export const dynamic = "force-dynamic";

const STATUS_TIMEOUT_MS = 10_000;

export async function GET(req: NextRequest): Promise<NextResponse> {
  const requestId = correlationId(req);
  const token = req.cookies.get(SESSION_COOKIE)?.value;

  if (!token) {
    const res = NextResponse.json({ authenticated: false, user: null });
    res.headers.set("x-request-id", requestId);
    // Remove a stale indicator that survived without its session cookie.
    clearSessionCookies(res);
    return res;
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_ORIGIN}/api/v1/auth/me`, {
      headers: {
        authorization: `Bearer ${token}`,
        "x-request-id": requestId,
      },
      cache: "no-store",
      signal: AbortSignal.timeout(STATUS_TIMEOUT_MS),
    });
  } catch {
    // Backend unreachable: the session cannot be validated. Report that
    // explicitly rather than guessing either way.
    return NextResponse.json(
      {
        authenticated: false,
        user: null,
        unavailable: true,
        request_id: requestId,
      },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    const res = NextResponse.json({ authenticated: false, user: null });
    res.headers.set("x-request-id", requestId);
    clearSessionCookies(res);
    res.headers.set("x-session-expired", "1");
    return res;
  }

  const user = (await upstream.json().catch(() => null)) as Record<
    string,
    unknown
  > | null;
  const res = NextResponse.json({ authenticated: true, user });
  res.headers.set("x-request-id", requestId);
  return res;
}
