"use client";

import { useEffect, useState } from "react";
import {
  API_BASE_URL,
  API_BASE_URL_HAS_API_PATH,
  API_BASE_URL_IS_DEFAULT,
} from "@/lib/api";

type Status =
  | "checking"
  | "connected"
  | "url_missing"
  | "unreachable"
  | "route_404"
  | "prefix_wrong"
  | "error";

// Shows whether the frontend can reach the backend API and distinguishes the
// common deployment misconfigurations: a missing backend URL, an unreachable or
// undeployed backend, a base URL that wrongly includes an /api path, and a
// reachable backend whose health route returns 404. The frontend reads the
// backend base URL from NEXT_PUBLIC_API_BASE_URL. It does not simulate data;
// pages fall back to seeded demo data where available.
export default function BackendStatusBanner() {
  const [status, setStatus] = useState<Status>("checking");
  const [version, setVersion] = useState<string | null>(null);
  const [httpStatus, setHttpStatus] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      // A base URL that already includes /api is a misconfiguration regardless
      // of reachability, since the client appends /api/v1 itself.
      if (API_BASE_URL_HAS_API_PATH) {
        if (active) setStatus("prefix_wrong");
        return;
      }
      try {
        const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
        if (!active) return;
        if (res.ok) {
          const body = (await res.json()) as { version?: string };
          setVersion(body.version ?? null);
          setStatus("connected");
          return;
        }
        // Reachable but the health route did not return 200. A 404 usually means
        // the base URL points at the wrong host or includes an API path.
        setHttpStatus(res.status);
        setStatus(res.status === 404 ? "route_404" : "error");
      } catch {
        if (!active) return;
        // Could not reach the host at all. If the URL was never set, call that
        // out specifically; otherwise the backend is not deployed or is down.
        setStatus(API_BASE_URL_IS_DEFAULT ? "url_missing" : "unreachable");
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  if (status === "checking") {
    return (
      <Box tone="neutral">Checking backend connection at {API_BASE_URL}...</Box>
    );
  }

  if (status === "connected") {
    return (
      <Box tone="ok">
        Backend connected{version ? ` (version ${version})` : ""}. Live review
        data is served from the API.
      </Box>
    );
  }

  if (status === "url_missing") {
    return (
      <Box tone="warn">
        Backend URL is not set, so the frontend is using the local default (
        {API_BASE_URL}). Set NEXT_PUBLIC_API_BASE_URL to the deployed backend
        origin. Pages fall back to seeded demo data where available.
      </Box>
    );
  }

  if (status === "prefix_wrong") {
    return (
      <Box tone="warn">
        The backend URL ({API_BASE_URL}) includes an /api path. Use the backend
        origin only, with no /api/v1: the frontend appends /api/v1 itself.
      </Box>
    );
  }

  if (status === "route_404") {
    return (
      <Box tone="warn">
        The backend at {API_BASE_URL} is reachable but /health returned 404.
        Confirm NEXT_PUBLIC_API_BASE_URL is the backend origin only, without
        /api/v1, and that the backend service is the FastAPI app. A 404 on the
        backend root is expected; /health and /api/v1 routes should respond.
      </Box>
    );
  }

  if (status === "error") {
    return (
      <Box tone="warn">
        The backend at {API_BASE_URL} responded with status {httpStatus}. Confirm
        the backend service is the FastAPI app and is healthy.
      </Box>
    );
  }

  // unreachable
  return (
    <Box tone="warn">
      Backend is not reachable at {API_BASE_URL}. It may not be deployed yet or it
      may be down. Confirm the backend service is running and that
      NEXT_PUBLIC_API_BASE_URL points at it. Pages fall back to seeded demo data
      where available.
    </Box>
  );
}

function Box({
  tone,
  children,
}: {
  tone: "neutral" | "ok" | "warn";
  children: React.ReactNode;
}) {
  const styles = {
    neutral: "border-slate-200 bg-slate-50 text-slate-500",
    ok: "border-water-200 bg-water-50 text-water-800",
    warn: "border-amber-200 bg-amber-50 text-amber-800",
  }[tone];
  return (
    <div className={`rounded-lg border px-4 py-2 text-sm ${styles}`}>
      {children}
    </div>
  );
}
