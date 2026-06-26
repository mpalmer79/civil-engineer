export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const PROJECT_ID = "proj_brookside_meadows";

// Sprint 5 local authentication. The access token is stored client-side in
// localStorage (a reasonable prototype-safe choice). Server components have no
// access to localStorage and run unauthenticated, which keeps the public demo
// visible; production should move toward hardened session handling or SSO. The
// token is never placed in a URL and never logged.
const AUTH_TOKEN_KEY = "civil_engineer_auth_token";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(AUTH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  } catch {
    // Storage unavailable (private mode); the session stays in memory only.
  }
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
  } catch {
    // Nothing to clear.
  }
}

export function authHeaders(
  extra?: Record<string, string>,
): Record<string, string> {
  const headers: Record<string, string> = { ...(extra ?? {}) };
  const token = getAuthToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export async function safeFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    // Backend unavailable. Callers fall back to static seed data.
    return null;
  }
}
