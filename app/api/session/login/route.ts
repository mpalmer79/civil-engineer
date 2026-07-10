// Session login endpoint. Exchanges credentials with the FastAPI backend and
// stores the returned access token in an HttpOnly cookie. The token itself is
// never included in the response body, so browser JavaScript never sees it.

import { NextRequest, NextResponse } from "next/server";

import { BACKEND_ORIGIN } from "@/lib/api/client";
import { applySessionCookies, csrfViolation } from "@/lib/server/session";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest): Promise<NextResponse> {
  const violation = csrfViolation(req);
  if (violation) {
    return NextResponse.json({ detail: violation }, { status: 403 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Invalid request body." }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_ORIGIN}/api/v1/auth/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "Backend unavailable." }, { status: 502 });
  }

  const payload = (await upstream.json().catch(() => ({}))) as {
    access_token?: string;
    user?: Record<string, unknown>;
    detail?: string;
  };

  if (!upstream.ok || !payload.access_token) {
    return NextResponse.json(
      { detail: payload.detail ?? "Sign in failed." },
      { status: upstream.ok ? 502 : upstream.status },
    );
  }

  const res = NextResponse.json({ user: payload.user ?? null });
  applySessionCookies(res, payload.access_token);
  return res;
}
