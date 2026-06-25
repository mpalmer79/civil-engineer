"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

type Status = "checking" | "connected" | "unavailable";

// Shows whether the frontend can reach the backend API. The frontend reads the
// backend base URL from NEXT_PUBLIC_API_BASE_URL, so this surfaces a clear
// message when the deployed backend is not reachable instead of failing
// silently. It does not simulate data; pages fall back to seeded demo data.
export default function BackendStatusBanner() {
  const [status, setStatus] = useState<Status>("checking");
  const [version, setVersion] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
        if (!res.ok) throw new Error("bad status");
        const body = (await res.json()) as { version?: string };
        if (active) {
          setStatus("connected");
          setVersion(body.version ?? null);
        }
      } catch {
        if (active) setStatus("unavailable");
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

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
      Backend is not reachable at {API_BASE_URL}. Set NEXT_PUBLIC_API_BASE_URL to
      the deployed backend URL and confirm the backend service is running. Pages
      fall back to seeded demo data where available.
    </div>
  );
}
