// Backend-for-frontend proxy. Every authenticated browser request goes through
// this same-origin route so the backend access token can live in an HttpOnly
// cookie instead of browser-readable storage. The proxy:
//
//   1. Rejects mutating requests that fail the CSRF gate.
//   2. Attaches the Authorization header from the session cookie server-side.
//   3. Forwards the response (status, JSON body, content type) unchanged, so
//      401/403/404/422 semantics from FastAPI reach the client intact.
//
// The token is never logged and never appears in a URL. Only /api/v1 paths
// are forwarded; this proxy is not an open relay.

import { NextRequest, NextResponse } from "next/server";

import { BACKEND_ORIGIN } from "@/lib/api/client";
import {
  MUTATING_METHODS,
  SESSION_COOKIE,
  csrfViolation,
} from "@/lib/server/session";

export const dynamic = "force-dynamic";

const FORWARDED_REQUEST_HEADERS = ["content-type", "accept"];

async function proxy(
  req: NextRequest,
  { params }: { params: { path: string[] } },
): Promise<NextResponse> {
  const segments = params.path ?? [];
  if (segments[0] !== "api") {
    return NextResponse.json(
      { detail: "Only backend API paths can be proxied." },
      { status: 404 },
    );
  }

  if (MUTATING_METHODS.has(req.method)) {
    const violation = csrfViolation(req);
    if (violation) {
      return NextResponse.json({ detail: violation }, { status: 403 });
    }
  }

  const target = new URL(
    `/${segments.map(encodeURIComponent).join("/")}`,
    BACKEND_ORIGIN,
  );
  target.search = req.nextUrl.search;

  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = req.headers.get(name);
    if (value) headers.set(name, value);
  }
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  if (token) headers.set("authorization", `Bearer ${token}`);

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body:
        req.method === "GET" || req.method === "HEAD"
          ? undefined
          : await req.arrayBuffer(),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "Backend unavailable." },
      { status: 502 },
    );
  }

  const responseHeaders = new Headers();
  const contentType = upstream.headers.get("content-type");
  if (contentType) responseHeaders.set("content-type", contentType);
  const disposition = upstream.headers.get("content-disposition");
  if (disposition) responseHeaders.set("content-disposition", disposition);

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export {
  proxy as GET,
  proxy as POST,
  proxy as PUT,
  proxy as PATCH,
  proxy as DELETE,
};
