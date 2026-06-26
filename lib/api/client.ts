const DEFAULT_API_BASE_URL = "http://localhost:8000";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;

// True when NEXT_PUBLIC_API_BASE_URL was not set, so the frontend fell back to
// the local default. The backend status banner uses this to tell a missing URL
// apart from a deployed-but-unreachable backend.
export const API_BASE_URL_IS_DEFAULT = !process.env.NEXT_PUBLIC_API_BASE_URL;

// True when the configured base URL wrongly includes an /api path. The frontend
// appends /api/v1 itself, so a base URL ending in /api or /api/v1 produces a
// doubled path. The banner surfaces this as a likely misconfiguration.
export const API_BASE_URL_HAS_API_PATH = /\/api(\/|$)/.test(API_BASE_URL);

export const PROJECT_ID = "proj_brookside_meadows";

export async function safeFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    // Backend unavailable. Callers fall back to static seed data.
    return null;
  }
}
