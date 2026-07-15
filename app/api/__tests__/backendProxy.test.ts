import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { POST, GET } from "@/app/api/backend/[...path]/route";

function proxyRequest(
  method: string,
  headers: Record<string, string> = {},
  init: { body?: BodyInit; url?: string } = {},
): NextRequest {
  return new NextRequest(init.url ?? "http://app.local/api/backend/api/v1/projects", {
    method,
    headers,
    body: init.body,
    // Node fetch requires duplex when a body stream is provided.
    ...(init.body ? { duplex: "half" } : {}),
  } as ConstructorParameters<typeof NextRequest>[1]);
}

const params = (segments: string[]) => ({
  params: Promise.resolve({ path: segments }),
});

function okUpstream(body: unknown = [], status = 200, headers: Record<string, string> = {}) {
  return vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status,
      headers: { "content-type": "application/json", ...headers },
    }),
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("CSRF gate", () => {
  it("rejects a mutating request without the CSRF header", async () => {
    const res = await POST(
      proxyRequest("POST", { host: "app.local" }),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(403);
    const body = (await res.json()) as { detail: string; request_id?: string };
    expect(body.detail).toBe("Missing CSRF protection header.");
    expect(body.request_id).toBeTruthy();
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

  it("accepts a valid same-origin mutation", async () => {
    vi.stubGlobal("fetch", okUpstream({ ok: true }, 201));
    const res = await POST(
      proxyRequest(
        "POST",
        {
          host: "app.local",
          origin: "http://app.local",
          "x-csrf-protection": "1",
          "content-type": "application/json",
        },
        { body: JSON.stringify({ a: 1 }) },
      ),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(201);
  });
});

describe("path validation", () => {
  it("refuses to proxy paths outside the backend API", async () => {
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["internal", "secrets"]),
    );
    expect(res.status).toBe(404);
  });

  it("rejects dot-segment traversal", async () => {
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "..", "internal"]),
    );
    expect(res.status).toBe(404);
  });

  it("rejects encoded traversal sequences", async () => {
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "v1", "%2e%2e", "admin"]),
    );
    expect(res.status).toBe(404);
  });

  it("rejects double-encoded traversal sequences", async () => {
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "v1", "%252e%252e"]),
    );
    expect(res.status).toBe(404);
  });

  it("rejects backslash segments", async () => {
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "v1", "a%5Cb"]),
    );
    expect(res.status).toBe(404);
  });

  it("rejects absolute URL scheme segments", async () => {
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "https:", "evil.example.net", "steal"]),
    );
    expect(res.status).toBe(404);
  });

  it("rejects empty segment tricks", async () => {
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "", "v1"]),
    );
    expect(res.status).toBe(404);
  });
});

describe("body limits", () => {
  it("rejects a declared oversized JSON body before reading it", async () => {
    const res = await POST(
      proxyRequest(
        "POST",
        {
          host: "app.local",
          "x-csrf-protection": "1",
          "content-type": "application/json",
          "content-length": String(3 * 1024 * 1024),
        },
        { body: "{}" },
      ),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(413);
  });

  it("rejects an undeclared oversized streamed body at the limit", async () => {
    // No Content-Length header: the streamed byte counter must catch it.
    const big = new Uint8Array(3 * 1024 * 1024);
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(big);
        controller.close();
      },
    });
    // The upstream fetch consumes the limited stream and errors mid-flight.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (_url, init: RequestInit) => {
        const reader = (init.body as ReadableStream<Uint8Array>).getReader();
        // Drain until the limiter errors.
         
        while (true) {
          const { done } = await reader.read();
          if (done) break;
        }
        return new Response("{}", { status: 200 });
      }),
    );
    const res = await POST(
      proxyRequest(
        "POST",
        {
          host: "app.local",
          "x-csrf-protection": "1",
          "content-type": "application/json",
        },
        { body: stream },
      ),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(413);
  });

  it("rejects multipart bodies on non-upload routes", async () => {
    const res = await POST(
      proxyRequest(
        "POST",
        {
          host: "app.local",
          "x-csrf-protection": "1",
          "content-type": "multipart/form-data; boundary=x",
        },
        { body: "--x--" },
      ),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(415);
  });

  it("allows multipart on the document upload route and streams it", async () => {
    let sawStream = false;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (_url, init: RequestInit) => {
        sawStream = init.body instanceof ReadableStream;
        if (init.body instanceof ReadableStream) {
          const reader = init.body.getReader();
           
          while (true) {
            const { done } = await reader.read();
            if (done) break;
          }
        }
        return new Response(JSON.stringify({ document_id: "doc_1" }), {
          status: 201,
          headers: { "content-type": "application/json" },
        });
      }),
    );
    const res = await POST(
      proxyRequest(
        "POST",
        {
          host: "app.local",
          "x-csrf-protection": "1",
          "content-type": "multipart/form-data; boundary=x",
        },
        {
          body: "--x\r\ncontent-disposition: form-data; name=f\r\n\r\nhello\r\n--x--",
          url: "http://app.local/api/backend/api/v1/projects/proj_1/documents/upload",
        },
      ),
      params(["api", "v1", "projects", "proj_1", "documents", "upload"]),
    );
    expect(res.status).toBe(201);
    // The body reached the upstream as a stream, never an ArrayBuffer.
    expect(sawStream).toBe(true);
  });

  it("never buffers request bodies through arrayBuffer", async () => {
    const { readFileSync } = await import("node:fs");
    const source = readFileSync("app/api/backend/[...path]/route.ts", "utf8");
    expect(source).not.toContain("arrayBuffer()");
  });
});

describe("header policy", () => {
  it("attaches the session cookie as a bearer token and preserves upstream status", async () => {
    const upstream = okUpstream({ detail: "Forbidden." }, 403);
    vi.stubGlobal("fetch", upstream);

    const res = await GET(
      proxyRequest("GET", {
        host: "app.local",
        cookie: "ce_session=tok_secret",
      }),
      params(["api", "v1", "me", "projects"]),
    );

    expect(res.status).toBe(403);
    const [, init] = upstream.mock.calls[0] as [URL, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.get("authorization")).toBe("Bearer tok_secret");
  });

  it("never forwards incoming cookies or authorization headers", async () => {
    const upstream = okUpstream([]);
    vi.stubGlobal("fetch", upstream);
    await GET(
      proxyRequest("GET", {
        host: "app.local",
        cookie: "ce_session=tok; tracking=abc",
        authorization: "Bearer attacker-supplied",
        "x-forwarded-host": "evil.example.net",
      }),
      params(["api", "v1", "projects"]),
    );
    const [, init] = upstream.mock.calls[0] as [URL, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.get("cookie")).toBeNull();
    expect(headers.get("x-forwarded-host")).toBeNull();
    // Authorization is rebuilt from the session cookie, not passed through.
    expect(headers.get("authorization")).toBe("Bearer tok");
  });

  it("strips backend Set-Cookie and implementation headers from responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("[]", {
          status: 200,
          headers: {
            "content-type": "application/json",
            "set-cookie": "backend_internal=1",
            server: "uvicorn",
            "x-internal-route": "secret",
          },
        }),
      ),
    );
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "v1", "projects"]),
    );
    expect(res.headers.get("set-cookie")).toBeNull();
    expect(res.headers.get("server")).toBeNull();
    expect(res.headers.get("x-internal-route")).toBeNull();
    expect(res.headers.get("content-type")).toContain("application/json");
  });

  it("propagates a valid client request ID and generates one otherwise", async () => {
    const upstream = okUpstream([]);
    vi.stubGlobal("fetch", upstream);
    const res = await GET(
      proxyRequest("GET", { host: "app.local", "x-request-id": "req-abc.123" }),
      params(["api", "v1", "projects"]),
    );
    expect(res.headers.get("x-request-id")).toBe("req-abc.123");
    const [, init] = upstream.mock.calls[0] as [URL, RequestInit];
    expect((init.headers as Headers).get("x-request-id")).toBe("req-abc.123");

    const res2 = await GET(
      proxyRequest("GET", {
        host: "app.local",
        "x-request-id": "<script>bad".repeat(20),
      }),
      params(["api", "v1", "projects"]),
    );
    expect(res2.headers.get("x-request-id")).toMatch(/^[0-9a-f-]{36}$/);
  });
});

describe("session invalidation", () => {
  it("clears session cookies when the backend returns 401 for a cookie-carrying request", async () => {
    vi.stubGlobal("fetch", okUpstream({ detail: "Authentication required." }, 401));
    const res = await GET(
      proxyRequest("GET", {
        host: "app.local",
        cookie: "ce_session=tok_expired",
      }),
      params(["api", "v1", "me", "projects"]),
    );
    expect(res.status).toBe(401);
    expect(res.headers.get("x-session-expired")).toBe("1");
    const setCookies = res.headers.getSetCookie();
    expect(setCookies.some((c) => c.startsWith("ce_session=;"))).toBe(true);
    expect(setCookies.some((c) => c.startsWith("ce_session_active=;"))).toBe(true);
  });

  it("does not clear cookies on a 401 without a session cookie", async () => {
    vi.stubGlobal("fetch", okUpstream({ detail: "Authentication required." }, 401));
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "v1", "me", "projects"]),
    );
    expect(res.status).toBe(401);
    expect(res.headers.get("x-session-expired")).toBeNull();
    expect(res.headers.getSetCookie()).toHaveLength(0);
  });
});

describe("failure semantics", () => {
  it("reports backend network failure as an explicit 502", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("down")));
    const res = await GET(
      proxyRequest("GET", { host: "app.local" }),
      params(["api", "v1", "projects"]),
    );
    expect(res.status).toBe(502);
    const body = (await res.json()) as { detail: string; request_id: string };
    expect(body.detail).toBe("Backend unavailable.");
    expect(body.request_id).toBeTruthy();
  });

  it("passes through 403, 404, and 422 semantics unchanged", async () => {
    for (const status of [403, 404, 422]) {
      vi.stubGlobal("fetch", okUpstream({ detail: "x" }, status));
      const res = await GET(
        proxyRequest("GET", { host: "app.local" }),
        params(["api", "v1", "projects"]),
      );
      expect(res.status).toBe(status);
    }
  });

  it("never places a token in the response body", async () => {
    vi.stubGlobal("fetch", okUpstream({ items: [] }));
    const res = await GET(
      proxyRequest("GET", {
        host: "app.local",
        cookie: "ce_session=tok_secret_value",
      }),
      params(["api", "v1", "projects"]),
    );
    const text = await res.text();
    expect(text).not.toContain("tok_secret_value");
  });
});
