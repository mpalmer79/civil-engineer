import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { POST as login } from "@/app/api/session/login/route";
import { GET as status } from "@/app/api/session/status/route";
import { POST as logout } from "@/app/api/session/logout/route";

function jsonRequest(
  url: string,
  body: unknown,
  headers: Record<string, string> = {},
): NextRequest {
  return new NextRequest(url, {
    method: "POST",
    headers: {
      host: "app.local",
      "content-type": "application/json",
      "x-csrf-protection": "1",
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

function backendLoginPayload(expiresInMinutes: unknown) {
  return {
    access_token: "tok_abc",
    token_type: "bearer",
    expires_in_minutes: expiresInMinutes,
    user: { user_id: "u1", email: "e@example.com", display_name: "Reviewer" },
  };
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("session login", () => {
  it("derives the cookie lifetime from the backend expires_in_minutes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(backendLoginPayload(45)), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      ),
    );
    const res = await login(
      jsonRequest("http://app.local/api/session/login", {
        email: "e@example.com",
        password: "pw",
      }),
    );
    expect(res.status).toBe(200);
    const cookies = res.headers.getSetCookie();
    const session = cookies.find((c) => c.startsWith("ce_session="));
    const indicator = cookies.find((c) => c.startsWith("ce_session_active="));
    expect(session).toContain("Max-Age=2700");
    expect(indicator).toContain("Max-Age=2700");
    expect(session).toContain("HttpOnly");
    expect(session?.toLowerCase()).toContain("samesite=lax");
    // The token never reaches the response body.
    const body = await res.text();
    expect(body).not.toContain("tok_abc");
  });

  it("rejects a login response with an invalid session lifetime", async () => {
    for (const bad of [undefined, 0, -10, "120", 60 * 24 * 40]) {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(
          new Response(JSON.stringify(backendLoginPayload(bad)), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
        ),
      );
      const res = await login(
        jsonRequest("http://app.local/api/session/login", {
          email: "e@example.com",
          password: "pw",
        }),
      );
      expect(res.status).toBe(502);
      expect(res.headers.getSetCookie()).toHaveLength(0);
    }
  });

  it("rejects login without the CSRF header", async () => {
    const req = new NextRequest("http://app.local/api/session/login", {
      method: "POST",
      headers: { host: "app.local", "content-type": "application/json" },
      body: JSON.stringify({ email: "e", password: "p" }),
    });
    const res = await login(req);
    expect(res.status).toBe(403);
  });

  it("passes backend authentication failures through", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Incorrect email or password." }), {
          status: 401,
          headers: { "content-type": "application/json" },
        }),
      ),
    );
    const res = await login(
      jsonRequest("http://app.local/api/session/login", {
        email: "e@example.com",
        password: "nope",
      }),
    );
    expect(res.status).toBe(401);
    const body = (await res.json()) as { detail: string };
    expect(body.detail).toBe("Incorrect email or password.");
  });
});

describe("session status", () => {
  it("reports unauthenticated and clears stale cookies when no session cookie exists", async () => {
    const res = await status(
      new NextRequest("http://app.local/api/session/status", {
        headers: { host: "app.local", cookie: "ce_session_active=1" },
      }),
    );
    expect(res.status).toBe(200);
    const body = (await res.json()) as { authenticated: boolean };
    expect(body.authenticated).toBe(false);
    const cookies = res.headers.getSetCookie();
    expect(cookies.some((c) => c.startsWith("ce_session_active=;"))).toBe(true);
  });

  it("validates the session against the backend and returns non-sensitive state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ user_id: "u1", email: "e@example.com", display_name: "R" }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      ),
    );
    const res = await status(
      new NextRequest("http://app.local/api/session/status", {
        headers: { host: "app.local", cookie: "ce_session=tok_valid" },
      }),
    );
    const body = (await res.json()) as { authenticated: boolean; user: unknown };
    expect(body.authenticated).toBe(true);
    expect(JSON.stringify(body)).not.toContain("tok_valid");
  });

  it("clears cookies and reports unauthenticated for an invalid token", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Invalid token." }), {
          status: 401,
          headers: { "content-type": "application/json" },
        }),
      ),
    );
    const res = await status(
      new NextRequest("http://app.local/api/session/status", {
        headers: {
          host: "app.local",
          cookie: "ce_session=tok_expired; ce_session_active=1",
        },
      }),
    );
    expect(res.status).toBe(200);
    const body = (await res.json()) as { authenticated: boolean };
    expect(body.authenticated).toBe(false);
    expect(res.headers.get("x-session-expired")).toBe("1");
    const cookies = res.headers.getSetCookie();
    expect(cookies.some((c) => c.startsWith("ce_session=;"))).toBe(true);
    expect(cookies.some((c) => c.startsWith("ce_session_active=;"))).toBe(true);
  });

  it("reports backend unavailability explicitly instead of guessing", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("down")));
    const res = await status(
      new NextRequest("http://app.local/api/session/status", {
        headers: { host: "app.local", cookie: "ce_session=tok" },
      }),
    );
    expect(res.status).toBe(502);
    const body = (await res.json()) as { authenticated: boolean; unavailable: boolean };
    expect(body.authenticated).toBe(false);
    expect(body.unavailable).toBe(true);
  });
});

describe("session logout", () => {
  it("clears both cookies", async () => {
    const res = await logout(
      new NextRequest("http://app.local/api/session/logout", {
        method: "POST",
        headers: { host: "app.local", "x-csrf-protection": "1" },
      }),
    );
    expect(res.status).toBe(200);
    const cookies = res.headers.getSetCookie();
    expect(cookies.some((c) => c.startsWith("ce_session=;"))).toBe(true);
    expect(cookies.some((c) => c.startsWith("ce_session_active=;"))).toBe(true);
  });

  it("rejects a cross-origin logout", async () => {
    const res = await logout(
      new NextRequest("http://app.local/api/session/logout", {
        method: "POST",
        headers: {
          host: "app.local",
          origin: "https://evil.example.net",
          "x-csrf-protection": "1",
        },
      }),
    );
    expect(res.status).toBe(403);
  });
});
