import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { POST, GET } from "@/app/api/backend/[...path]/route";

function proxyRequest(
  method: string,
  headers: Record<string, string> = {},
  url = "http://app.local/api/backend/api/v1/projects",
): NextRequest {
  return new NextRequest(url, { method, headers });
}

const params = (segments: string[]) => ({ params: { path: segments } });

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("backend proxy CSRF gate", () => {
  it("rejects a mutating request without the CSRF header", async () => {
    const res = await POST(
      proxyRequest("POST", { host: "app.local" }),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(403);
    const body = (await res.json()) as { detail: string };
    expect(body.detail).toBe("Missing CSRF protection header.");
  });

  it("rejects a cross-origin mutating request", async () => {
    const res = await POST(
      proxyRequest("POST", {
        host: "app.local",
        origin: "https://evil.example.net",
        "x-csrf-protection": "1",
      }),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(403);
  });
});

describe("backend proxy forwarding", () => {
  it("refuses to proxy paths outside the backend API", async () => {
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["internal", "secrets"]),
    );
    expect(res.status).toBe(404);
  });

  it("attaches the session cookie as a bearer token and preserves upstream status", async () => {
    const upstream = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Forbidden." }), {
        status: 403,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", upstream);

    const res = await GET(
      proxyRequest("GET", {
        host: "app.local",
        cookie: "ce_session=tok_secret",
      }),
      params(["api", "v1", "me", "projects"]),
    );

    // The upstream 403 reaches the caller unchanged, so permission states are
    // distinguishable from missing data.
    expect(res.status).toBe(403);
    const [, init] = upstream.mock.calls[0] as [URL, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.get("authorization")).toBe("Bearer tok_secret");
  });

  it("forwards unauthenticated requests without an Authorization header", async () => {
    const upstream = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", upstream);

    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(200);
    const [, init] = upstream.mock.calls[0] as [URL, RequestInit];
    expect((init.headers as Headers).get("authorization")).toBeNull();
  });

  it("reports backend unavailability as an explicit 502", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("down")));
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(502);
    const body = (await res.json()) as { detail: string };
    expect(body.detail).toBe("Backend unavailable.");
  });
});
