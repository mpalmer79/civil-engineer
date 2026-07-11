import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getCurrentUser,
  grantProjectAccess,
  isSignedIn,
  loginUser,
  logoutUser,
  registerUser,
} from "@/lib/api";
import { CSRF_HEADER, SESSION_INDICATOR_COOKIE } from "@/lib/api/client";

function mockFetchOnce(payload: unknown, ok = true, status = 200) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  } as Response);
}

function setIndicatorCookie() {
  document.cookie = `${SESSION_INDICATOR_COOKIE}=1; path=/`;
}

function clearIndicatorCookie() {
  document.cookie = `${SESSION_INDICATOR_COOKIE}=; path=/; max-age=0`;
}

beforeEach(() => {
  clearIndicatorCookie();
});

afterEach(() => {
  vi.restoreAllMocks();
  clearIndicatorCookie();
});

describe("loginUser", () => {
  it("posts credentials to the same-origin session endpoint with the CSRF header", async () => {
    mockFetchOnce({
      user: {
        user_id: "user_1",
        email: "reviewer@example.com",
        display_name: "Demo Reviewer",
        is_active: true,
        is_demo_user: true,
      },
    });
    const result = await loginUser("reviewer@example.com", "password123");
    expect(result.ok).toBe(true);
    expect(result.data?.user.displayName).toBe("Demo Reviewer");
    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    expect(call[0]).toBe("/api/session/login");
    const init = call[1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers[CSRF_HEADER]).toBe("1");
    const body = JSON.parse(init.body as string);
    expect(body.email).toBe("reviewer@example.com");
    expect(body.password).toBe("password123");
  });

  it("never exposes an access token to the caller", async () => {
    mockFetchOnce({
      user: { user_id: "u", email: "e", display_name: "d" },
    });
    const result = await loginUser("e@example.com", "password123");
    expect(result.ok).toBe(true);
    expect(JSON.stringify(result)).not.toContain("access_token");
    expect(window.localStorage.getItem("civil_engineer_auth_token")).toBeNull();
  });

  it("surfaces an authentication error", async () => {
    mockFetchOnce({ detail: "Incorrect email or password." }, false, 401);
    const result = await loginUser("x@example.com", "nope");
    expect(result.ok).toBe(false);
    expect(result.error).toBe("Incorrect email or password.");
  });
});

describe("registerUser", () => {
  it("posts to the same-origin session register endpoint", async () => {
    mockFetchOnce({
      user: {
        user_id: "user_2",
        email: "new@example.com",
        display_name: "New User",
      },
    });
    const result = await registerUser({
      email: "new@example.com",
      displayName: "New User",
      password: "password123",
      organizationName: "Town",
    });
    expect(result.ok).toBe(true);
    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    expect(call[0]).toBe("/api/session/register");
    const body = JSON.parse((call[1] as RequestInit).body as string);
    expect(body.organization_name).toBe("Town");
  });
});

describe("logoutUser", () => {
  it("posts to the session logout endpoint", async () => {
    mockFetchOnce({ ok: true });
    await logoutUser();
    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    expect(call[0]).toBe("/api/session/logout");
    expect((call[1] as RequestInit).method).toBe("POST");
  });
});

describe("isSignedIn", () => {
  it("reflects the non-sensitive session indicator cookie", () => {
    expect(isSignedIn()).toBe(false);
    setIndicatorCookie();
    expect(isSignedIn()).toBe(true);
  });
});

describe("getCurrentUser", () => {
  it("returns null without a session indicator and does not call fetch", async () => {
    const spy = vi.fn();
    globalThis.fetch = spy;
    const user = await getCurrentUser();
    expect(user).toBeNull();
    expect(spy).not.toHaveBeenCalled();
  });

  it("reads validated session state from the session status endpoint", async () => {
    setIndicatorCookie();
    mockFetchOnce({
      authenticated: true,
      user: {
        user_id: "u",
        email: "e@example.com",
        display_name: "Signed In",
        is_active: true,
        is_demo_user: false,
      },
    });
    const user = await getCurrentUser();
    expect(user?.displayName).toBe("Signed In");
    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    // Session truth comes from the server-validated status endpoint; no
    // Authorization header is constructed in browser code.
    expect(String(call[0])).toBe("/api/session/status");
    const headers = ((call[1] as RequestInit | undefined)?.headers ?? {}) as Record<
      string,
      string
    >;
    expect(headers.Authorization).toBeUndefined();
  });

  it("returns null when the validated session is unauthenticated", async () => {
    setIndicatorCookie();
    mockFetchOnce({ authenticated: false, user: null });
    const user = await getCurrentUser();
    expect(user).toBeNull();
  });
});

describe("grantProjectAccess", () => {
  it("sends the access level and target user", async () => {
    mockFetchOnce({
      project_access_id: "pacc_1",
      project_id: "proj_1",
      user_id: "user_target",
      access_level: "reviewer",
      is_active: true,
    });
    const result = await grantProjectAccess("proj_1", {
      accessLevel: "reviewer",
      userId: "user_target",
    });
    expect(result.ok).toBe(true);
    expect(result.data?.accessLevel).toBe("reviewer");
    const body = JSON.parse(
      (
        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
          .calls[0][1] as RequestInit
      ).body as string,
    );
    expect(body.access_level).toBe("reviewer");
    expect(body.user_id).toBe("user_target");
  });
});
