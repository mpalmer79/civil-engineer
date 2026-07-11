// Session login endpoint. Exchanges credentials with the FastAPI backend and
// stores the returned access token in an HttpOnly cookie whose lifetime is
// derived from the backend's expires_in_minutes. The token itself is never
// included in the response body, so browser JavaScript never sees it.

import { NextRequest, NextResponse } from "next/server";

import { BACKEND_ORIGIN } from "@/lib/api/client";
import {
  applySessionCookies,
  correlationId,
  csrfViolation,
  sessionMaxAgeSeconds,
} from "@/lib/server/session";

export const dynamic = "force-dynamic";

const AUTH_TIMEOUT_MS = 10_000;

export async function POST(req: NextRequest): Promise<NextResponse> {
  const requestId = correlationId(req);
  const violation = csrfViolation(req);
  if (violation) {
    return NextResponse.json(
      { detail: violation, request_id: requestId },
      { status: 403 },
    );
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { detail: "Invalid request body.", request_id: requestId },
      { status: 400 },
    );
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_ORIGIN}/api/v1/auth/login`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-request-id": requestId },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(AUTH_TIMEOUT_MS),
    });
  } catch {
    return NextResponse.json(
      { detail: "Backend unavailable.", request_id: requestId },
      { status: 502 },
    );
  }

  const payload = (await upstream.json().catch(() => ({}))) as {
    access_token?: string;
    expires_in_minutes?: unknown;
    user?: Record<string, unknown>;
    detail?: string;
  };

  if (!upstream.ok || !payload.access_token) {
    return NextResponse.json(
      { detail: payload.detail ?? "Sign in failed.", request_id: requestId },
      { status: upstream.ok ? 502 : upstream.status },
    );
  }

  // The cookie lifetime must come from the backend's stated token lifetime.
  // A missing or unreasonable value is a contract violation, not something to
  // paper over with a default that could outlive the token.
  const maxAge = sessionMaxAgeSeconds(payload.expires_in_minutes);
  if (maxAge === null) {
    return NextResponse.json(
      {
        detail: "The backend returned an invalid session lifetime.",
        request_id: requestId,
      },
      { status: 502 },
    );
  }

  const res = NextResponse.json({ user: payload.user ?? null });
  res.headers.set("x-request-id", requestId);
  applySessionCookies(res, payload.access_token, maxAge);
  return res;
}
