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
// missing, validation, server, and offline states instead of collapsing every
// failure into null.
export type ApiFailureKind =
  | "unauthenticated"
  | "forbidden"
  | "not_found"
  | "validation"
  | "server"
  | "network";

export type ApiSuccess<T> = {
  ok: true;
  data: T;
  source: "backend";
  status: number;
};

export type ApiFailure = {
  ok: false;
  kind: ApiFailureKind;
  status?: number;
  message: string;
};

export type ApiResult<T> = ApiSuccess<T> | ApiFailure;

function failureKind(status: number): ApiFailureKind {
  if (status === 401) return "unauthenticated";
  if (status === 403) return "forbidden";
  if (status === 404) return "not_found";
  if (status === 422 || status === 400) return "validation";
  return "server";
}

async function failureMessage(res: Response): Promise<string> {
  try {
    const parsed = (await res.json()) as { detail?: unknown };
    if (typeof parsed.detail === "string" && parsed.detail) return parsed.detail;
  } catch {
    // Fall through to the generic message.
  }
  return `Request failed (${res.status}).`;
}

// Typed fetch. Preserves status and error category. Use this for new code and
// for any path that needs to distinguish failure modes.
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
      return {
        ok: false,
        kind: failureKind(res.status),
        status: res.status,
        message: await failureMessage(res),
      };
    }
    return {
      ok: true,
      data: (await res.json()) as T,
      source: "backend",
      status: res.status,
    };
  } catch {
    return {
      ok: false,
      kind: "network",
      message: "Backend unavailable.",
    };
  }
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

// Transitional wrapper kept for modules that still model absence as null.
// It must never be used to substitute seeded data for a failed authenticated
// request; callers that need failure detail should migrate to apiFetch.
export async function safeFetch<T>(path: string): Promise<T | null> {
  const result = await apiFetch<T>(path);
  return result.ok ? result.data : null;
}
