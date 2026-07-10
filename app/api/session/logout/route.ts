// Session logout endpoint. Clears the HttpOnly session cookie and the
// client-readable indicator cookie. The backend uses stateless signed tokens,
// so removing the cookie ends the browser session.

import { NextRequest, NextResponse } from "next/server";

import { clearSessionCookies, csrfViolation } from "@/lib/server/session";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest): Promise<NextResponse> {
  const violation = csrfViolation(req);
  if (violation) {
    return NextResponse.json({ detail: violation }, { status: 403 });
  }

  const res = NextResponse.json({ ok: true });
  clearSessionCookies(res);
  return res;
}
