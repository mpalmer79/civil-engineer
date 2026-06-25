"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL, PROJECT_ID } from "@/lib/api";

// The frontend reads the backend origin from NEXT_PUBLIC_API_BASE_URL. When the
// variable is not set, API_BASE_URL falls back to the local default, so an
// unset variable in a deployment looks like a localhost URL here.
const ENV_VAR_SET = Boolean(process.env.NEXT_PUBLIC_API_BASE_URL);

type Status =
  | "checking"
  | "connected"
  | "url-missing"
  | "unreachable"
  | "health-404"
  | "prefix-wrong";

// Shows whether the frontend can reach the backend API and, when it cannot,
// distinguishes the likely cause so a misconfiguration is easy to fix:
// the backend URL is missing, the backend is not reachable at all, the /health
// route returned 404, or the API prefix looks wrong. It does not simulate data;
// pages fall back to seeded demo data where available.
export default function BackendStatusBanner() {
  const [status, setStatus] = useState<Status>("checking");
  const [version, setVersion] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
        if (res.ok) {
          const body = (await res.json()) as { version?: string };
          if (active) {
            setStatus("connected");
            setVersion(body.version ?? null);
          }
          return;
        }
        // /health is reachable but did not return ok. Probe an /api/v1 route to
        // tell a missing health route apart from a wrong API prefix.
        if (res.status === 404) {
          let apiReachable = false;
          try {
            const apiRes = await fetch(
              `${API_BASE_URL}/api/v1/projects/${PROJECT_ID}`,
              { cache: "no-store" },
            );
            apiReachable = apiRes.ok;
          } catch {
            apiReachable = false;
          }
          if (active) setStatus(apiReachable ? "health-404" : "prefix-wrong");
          return;
        }
        if (active) setStatus("unreachable");
      } catch {
        // No response at all. If the env var was never set, the most likely
        // cause is a missing backend URL rather than a down backend.
        if (active) setStatus(ENV_VAR_SET ? "unreachable" : "url-missing");
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  if (status === "checking") {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-500">
        Checking backend connection at {API_BASE_URL}...
      </div>
    );
  }

  if (status === "connected") {
    return (
      <div className="rounded-lg border border-water-200 bg-water-50 px-4 py-2 text-sm text-water-800">
        Backend connected{version ? ` (version ${version})` : ""}. Live review
        data is served from the API.
      </div>
    );
  }

  const messages: Record<Exclude<Status, "checking" | "connected">, string> = {
    "url-missing":
      `Backend URL is not set. NEXT_PUBLIC_API_BASE_URL is missing, so the ` +
      `frontend is trying the local default ${API_BASE_URL}. Set it to the ` +
      `deployed backend origin (no /api/v1 path).`,
    unreachable:
      `Backend is not reachable at ${API_BASE_URL}. The backend may not be ` +
      `deployed or running. Confirm the backend service is up and that ` +
      `NEXT_PUBLIC_API_BASE_URL points at its public origin.`,
    "health-404":
      `Backend reached at ${API_BASE_URL}, but /health returned 404. The API ` +
      `routes respond, so the service is up; the health route may be ` +
      `misconfigured. A 404 on the root / is expected.`,
    "prefix-wrong":
      `Backend reached at ${API_BASE_URL}, but neither /health nor the ` +
      `/api/v1 routes responded as expected. The API prefix or the backend ` +
      `URL may be wrong. NEXT_PUBLIC_API_BASE_URL must be the origin only, ` +
      `with no /api/v1 path.`,
  };

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
      {messages[status]} Pages fall back to seeded demo data where available.
    </div>
  );
}
