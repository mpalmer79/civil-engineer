// Core API client infrastructure.
//
// Session architecture: the browser never holds a backend credential. All
// authenticated browser requests go to the same-origin Next.js
// backend-for-frontend proxy (/api/backend/...), which attaches the backend
// access token from an HttpOnly session cookie that browser JavaScript cannot
// read. Server-side code (route handlers, server components) talks to the
// FastAPI origin directly. See docs/adr/0003-secure-session-architecture.md.

// The FastAPI origin. Server-side only consumers use this directly; the
// browser goes through the same-origin proxy instead.
export const BACKEND_ORIGIN =
  process.env.BACKEND_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

// Base URL prepended to /api/v1 paths by every API module. In the browser this
// is the same-origin proxy so the HttpOnly session cookie can authenticate the
// request; on the server it is the backend origin (server rendering is
// unauthenticated and only sees public demo data).
export const API_BASE_URL =
  typeof window === "undefined" ? BACKEND_ORIGIN : "/api/backend";

export const PROJECT_ID = "proj_brookside_meadows";

// Non-sensitive, client-readable indicator that a session cookie exists. The
// real session cookie is HttpOnly; this companion cookie carries no secret and
// only lets the UI skip requests that would certainly return 401.
export const SESSION_INDICATOR_COOKIE = "ce_session_active";

export function hasSessionIndicator(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie
    .split(";")
    .some((part) => part.trim().startsWith(`${SESSION_INDICATOR_COOKIE}=`));
}

// Header name and value required by the proxy on every mutating request.
// Cross-site attackers cannot set custom headers without a CORS preflight the
// browser will refuse, so requiring this header (plus the proxy's same-origin
// check) blocks CSRF. See docs/adr/0003-secure-session-architecture.md.
export const CSRF_HEADER = "x-csrf-protection";

// Builds request headers for API calls. Authentication is no longer attached
// here: the browser cannot read the session cookie, and the proxy injects the
// Authorization header server-side. The CSRF marker rides along on every call
// so mutating requests pass the proxy's CSRF gate.
export function authHeaders(
  extra?: Record<string, string>,
): Record<string, string> {
  return { [CSRF_HEADER]: "1", ...(extra ?? {}) };
}

// Typed result model for API calls. Failures preserve the HTTP status and an
// error category so pages can render explicit unauthenticated, forbidden,
// missing, validation, conflict, rate-limited, timeout, unavailable, and
// invalid-payload states instead of collapsing every failure into null.
export type ApiFailureKind =
  | "unauthenticated"
  | "forbidden"
  | "not_found"
  | "validation"
  | "conflict"
  | "rate_limited"
  | "timeout"
  | "unavailable"
  | "server"
  | "network"
  | "invalid_response";

export type ApiSuccess<T> = {
  ok: true;
  data: T;
  source: "backend";
  status: number;
  requestId?: string;
};

export type ApiFailure = {
  ok: false;
  kind: ApiFailureKind;
  status?: number;
  message: string;
  requestId?: string;
  // Field-level details from a 422 validation response, when present.
  validationDetails?: unknown;
  // Whether retrying the same request could plausibly succeed.
  retryable: boolean;
};

export type ApiResult<T> = ApiSuccess<T> | ApiFailure;

function failureKind(status: number): ApiFailureKind {
  if (status === 401) return "unauthenticated";
  if (status === 403) return "forbidden";
  if (status === 404) return "not_found";
  if (status === 422 || status === 400) return "validation";
  if (status === 409) return "conflict";
  if (status === 429) return "rate_limited";
  if (status === 504) return "timeout";
  if (status === 502 || status === 503) return "unavailable";
  return "server";
}

const RETRYABLE_KINDS = new Set<ApiFailureKind>([
  "timeout",
  "unavailable",
  "rate_limited",
  "network",
  "server",
]);

async function failureFrom(res: Response): Promise<ApiFailure> {
  const kind = failureKind(res.status);
  let message = `Request failed (${res.status}).`;
  let requestId = res.headers?.get?.("x-request-id") ?? undefined;
  let validationDetails: unknown;
  try {
    const parsed = (await res.json()) as {
      detail?: unknown;
      request_id?: unknown;
    };
    if (typeof parsed.detail === "string" && parsed.detail) {
      message = parsed.detail;
    } else if (parsed.detail !== undefined && kind === "validation") {
      // FastAPI 422 responses carry structured field errors in detail.
      validationDetails = parsed.detail;
      message = "The request failed validation.";
    }
    if (!requestId && typeof parsed.request_id === "string") {
      requestId = parsed.request_id;
    }
  } catch {
    // Keep the generic message.
  }
  return {
    ok: false,
    kind,
    status: res.status,
    message,
    requestId,
    validationDetails,
    retryable: RETRYABLE_KINDS.has(kind),
  };
}

// Typed fetch. Preserves status, error category, and correlation ID. Use this
// for every read; mutations may use it or their module-level result shapes.
export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      ...init,
      headers: authHeaders(
        (init?.headers as Record<string, string> | undefined) ?? undefined,
      ),
    });
    if (!res.ok) {
      return failureFrom(res);
    }
    let data: T;
    try {
      data = (await res.json()) as T;
    } catch {
      return {
        ok: false,
        kind: "invalid_response",
        status: res.status,
        message: "The backend returned a response that could not be read.",
        requestId: res.headers?.get?.("x-request-id") ?? undefined,
        retryable: false,
      };
    }
    return {
      ok: true,
      data,
      source: "backend",
      status: res.status,
      requestId: res.headers?.get?.("x-request-id") ?? undefined,
    };
  } catch {
    return {
      ok: false,
      kind: "network",
      message: "Backend unavailable.",
      retryable: true,
    };
  }
}

// Typed read with a mapping and validation step. The mapper converts the wire
// payload into the view model; a mapper that throws (including the assert
// helpers below) turns a structurally invalid backend payload into an explicit
// invalid_response failure instead of propagating undefined fields into the UI.
export async function apiGetMapped<W, T>(
  path: string,
  map: (wire: W) => T,
): Promise<ApiResult<T>> {
  const result = await apiFetch<W>(path);
  if (!result.ok) return result;
  try {
    return { ...result, data: map(result.data) };
  } catch {
    return {
      ok: false,
      kind: "invalid_response",
      status: result.status,
      message: "The backend returned an unexpected payload shape.",
      requestId: result.requestId,
      retryable: false,
    };
  }
}

// Minimal runtime assertions for high-risk payload mapping. Mappers use these
// on required fields so an invalid payload fails loudly through apiGetMapped.
export function requireString(value: unknown, field: string): string {
  if (typeof value !== "string") {
    throw new Error(`Expected string field: ${field}`);
  }
  return value;
}

export function requireArray(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new Error(`Expected array field: ${field}`);
  }
  return value;
}

export function requireRecord(
  value: unknown,
  field: string,
): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`Expected object field: ${field}`);
  }
  return value as Record<string, unknown>;
}

// Source marker for the public Brookside Meadows demo surfaces. The demo data
// is seeded either way; the marker records whether it came from the connected
// backend seed or from the local fixture snapshot so pages can disclose it.
// Authenticated project and organization surfaces never use this model: their
// failures surface as explicit ApiFailure states, never as substituted data.
export type DemoDataSource = "backend_seeded" | "demo_fixture";

export type DemoSourced<T> = {
  data: T;
  source: DemoDataSource;
};
