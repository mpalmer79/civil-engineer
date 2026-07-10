// Backend-for-frontend proxy. Every authenticated browser request goes through
// this same-origin route so the backend access token can live in an HttpOnly
// cookie instead of browser-readable storage.
//
// This route is security infrastructure. Its policy is documented in
// docs/security/BFF_PROXY_THREAT_MODEL.md and enforced by
// app/api/__tests__/backendProxy.test.ts. Summary:
//
//   1. Fixed upstream: only the configured FastAPI origin, only /api paths,
//      strict segment validation against traversal and absolute-URL tricks.
//   2. CSRF gate on mutations (trusted-origin check plus custom header).
//   3. Route-class body limits enforced on the declared Content-Length and
//      again on the streamed byte count; uploads stream, never buffer.
//   4. Route-class upstream timeouts with typed 504 responses, linked to the
//      client abort signal.
//   5. Allowlisted request and response headers; the Authorization header is
//      built only from the session cookie; backend Set-Cookie never passes.
//   6. Backend 401 with a session cookie present clears the session cookies
//      and marks the response so the client renders an explicit signed-out
//      state.
//   7. A correlation ID rides every request, upstream and back.

import { NextRequest, NextResponse } from "next/server";

import { BACKEND_ORIGIN } from "@/lib/api/client";
import {
  MUTATING_METHODS,
  SESSION_COOKIE,
  clearSessionCookies,
  correlationId,
  csrfViolation,
} from "@/lib/server/session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const FORWARDED_REQUEST_HEADERS = ["content-type", "accept"] as const;
const FORWARDED_RESPONSE_HEADERS = [
  "content-type",
  "content-disposition",
  "cache-control",
] as const;

type RoutePolicy = {
  name: string;
  maxBodyBytes: number;
  timeoutMs: number;
  allowMultipart: boolean;
};

// Route classes. Upload limits match the backend configuration
// (MAX_PROJECT_UPLOAD_BYTES 25 MB, CAD_MAX_UPLOAD_BYTES 5 MB); the backend
// remains the final validator.
const DOCUMENT_UPLOAD = /^api\/v1\/projects\/[^/]+\/documents\/upload$/;
const CAD_UPLOAD = /^api\/v1\/projects\/[^/]+\/cad-files\/upload$/;
const AUTH_PATH = /^api\/v1\/auth\//;

const POLICIES = {
  auth: { name: "auth", maxBodyBytes: 64 * 1024, timeoutMs: 10_000, allowMultipart: false },
  json: { name: "json", maxBodyBytes: 2 * 1024 * 1024, timeoutMs: 30_000, allowMultipart: false },
  documentUpload: { name: "document-upload", maxBodyBytes: 25_000_000, timeoutMs: 120_000, allowMultipart: true },
  cadUpload: { name: "cad-upload", maxBodyBytes: 5_000_000, timeoutMs: 120_000, allowMultipart: true },
} satisfies Record<string, RoutePolicy>;

function policyFor(path: string): RoutePolicy {
  if (DOCUMENT_UPLOAD.test(path)) return POLICIES.documentUpload;
  if (CAD_UPLOAD.test(path)) return POLICIES.cadUpload;
  if (AUTH_PATH.test(path)) return POLICIES.auth;
  return POLICIES.json;
}

// Strict path validation. Decodes each segment up to twice to catch
// double-encoded traversal, then rejects anything that is empty, a dot
// segment, contains a slash or backslash after decoding, or looks like an
// absolute URL scheme.
function validatedPath(segments: string[]): string | null {
  if (segments.length < 2 || segments[0] !== "api") return null;
  const clean: string[] = [];
  for (const raw of segments) {
    if (typeof raw !== "string" || raw.length === 0) return null;
    let decoded = raw;
    for (let i = 0; i < 2; i += 1) {
      try {
        const next = decodeURIComponent(decoded);
        if (next === decoded) break;
        decoded = next;
      } catch {
        return null;
      }
    }
    if (decoded === "." || decoded === "..") return null;
    if (/[/\\]/.test(decoded)) return null;
    if (/^https?:$/i.test(decoded)) return null;
    clean.push(encodeURIComponent(decoded));
  }
  return clean.join("/");
}

function errorResponse(
  status: number,
  detail: string,
  requestId: string,
): NextResponse {
  const res = NextResponse.json({ detail, request_id: requestId }, { status });
  res.headers.set("x-request-id", requestId);
  return res;
}

// Wraps a request body stream with a byte counter that aborts when the policy
// limit is exceeded. Content-Length is checked first, but it is client
// controlled, so the streamed count is the real enforcement.
function limitedStream(
  body: ReadableStream<Uint8Array>,
  limit: number,
  onExceeded: () => void,
): ReadableStream<Uint8Array> {
  let total = 0;
  return body.pipeThrough(
    new TransformStream<Uint8Array, Uint8Array>({
      transform(chunk, controller) {
        total += chunk.byteLength;
        if (total > limit) {
          onExceeded();
          controller.error(new Error("body limit exceeded"));
          return;
        }
        controller.enqueue(chunk);
      },
    }),
  );
}

// Composes abort signals. AbortSignal.any is used where available (Node 20+);
// the manual fallback covers test environments whose AbortSignal lacks it.
function anySignal(signals: AbortSignal[]): AbortSignal {
  const native = (AbortSignal as unknown as { any?: (s: AbortSignal[]) => AbortSignal }).any;
  if (typeof native === "function") return native.call(AbortSignal, signals);
  const controller = new AbortController();
  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort(signal.reason);
      break;
    }
    signal.addEventListener("abort", () => controller.abort(signal.reason), {
      once: true,
    });
  }
  return controller.signal;
}

async function proxy(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
): Promise<NextResponse> {
  const requestId = correlationId(req);
  const { path: segments } = await params;

  const path = validatedPath(segments ?? []);
  if (path === null) {
    return errorResponse(404, "Only backend API paths can be proxied.", requestId);
  }

  const policy = policyFor(path);

  if (MUTATING_METHODS.has(req.method)) {
    const violation = csrfViolation(req);
    if (violation) return errorResponse(403, violation, requestId);
  }

  const contentType = req.headers.get("content-type") ?? "";
  const isMultipart = contentType.toLowerCase().startsWith("multipart/");
  if (isMultipart && !policy.allowMultipart) {
    return errorResponse(
      415,
      "Multipart uploads are not supported on this route.",
      requestId,
    );
  }

  // Reject a declared oversized body before reading anything. Content-Length
  // is not trusted as the only protection; the stream below counts bytes too.
  const declaredLength = Number(req.headers.get("content-length") ?? "0");
  if (Number.isFinite(declaredLength) && declaredLength > policy.maxBodyBytes) {
    return errorResponse(413, "Request body exceeds the allowed size.", requestId);
  }

  const target = new URL(`/${path}`, BACKEND_ORIGIN);
  target.search = req.nextUrl.search;

  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = req.headers.get(name);
    if (value) headers.set(name, value);
  }
  headers.set("x-request-id", requestId);
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  if (token) headers.set("authorization", `Bearer ${token}`);

  const timeoutSignal = AbortSignal.timeout(policy.timeoutMs);
  const signal = anySignal([timeoutSignal, req.signal]);

  let bodyLimitExceeded = false;
  const hasBody = req.method !== "GET" && req.method !== "HEAD" && req.body;
  const body = hasBody
    ? limitedStream(req.body as ReadableStream<Uint8Array>, policy.maxBodyBytes, () => {
        bodyLimitExceeded = true;
      })
    : undefined;

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      cache: "no-store",
      signal,
      // Required by the Node fetch implementation when the body is a stream.
      ...(body ? { duplex: "half" as const } : {}),
    });
  } catch {
    if (bodyLimitExceeded) {
      return errorResponse(413, "Request body exceeds the allowed size.", requestId);
    }
    if (timeoutSignal.aborted) {
      return errorResponse(
        504,
        "The backend did not respond in time.",
        requestId,
      );
    }
    if (req.signal.aborted) {
      // The browser abandoned the request; the upstream call was aborted with
      // it. The response is unused, but return a well-formed one.
      return errorResponse(502, "Client closed request.", requestId);
    }
    return errorResponse(502, "Backend unavailable.", requestId);
  }

  const responseHeaders = new Headers();
  for (const name of FORWARDED_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }
  responseHeaders.set("x-request-id", requestId);

  const res = new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });

  // A 401 for a request that carried a session cookie means the token is
  // expired or invalid. Clear the cookies so the stale indicator cannot keep
  // claiming a session, and mark the response for the client's session
  // expired handling.
  if (upstream.status === 401 && token) {
    clearSessionCookies(res);
    res.headers.set("x-session-expired", "1");
  }

  return res;
}

export {
  proxy as GET,
  proxy as POST,
  proxy as PUT,
  proxy as PATCH,
  proxy as DELETE,
};
