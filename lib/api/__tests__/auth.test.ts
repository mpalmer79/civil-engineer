import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearAuthToken,
  getAuthToken,
  getCurrentUser,
  grantProjectAccess,
  loginUser,
  logoutUser,
  registerUser,
} from "@/lib/api";

function mockFetchOnce(payload: unknown, ok = true, status = 200) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  } as Response);
}

beforeEach(() => {
  clearAuthToken();
});

afterEach(() => {
  vi.restoreAllMocks();
  clearAuthToken();
});

describe("loginUser", () => {
  it("sends the expected payload and stores the token", async () => {
    mockFetchOnce({
      access_token: "tok_abc",
      token_type: "bearer",
      expires_in_minutes: 120,
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
    expect(getAuthToken()).toBe("tok_abc");
    const body = JSON.parse(
      (
        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
          .calls[0][1] as RequestInit
      ).body as string,
    );
    expect(body.email).toBe("reviewer@example.com");
    expect(body.password).toBe("password123");
  });

  it("surfaces an authentication error", async () => {
    mockFetchOnce({ detail: "Incorrect email or password." }, false, 401);
    const result = await loginUser("x@example.com", "nope");
    expect(result.ok).toBe(false);
    expect(result.error).toBe("Incorrect email or password.");
    expect(getAuthToken()).toBeNull();
  });
});

describe("registerUser", () => {
  it("stores the token on success", async () => {
    mockFetchOnce({
      access_token: "tok_reg",
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
    expect(getAuthToken()).toBe("tok_reg");
    const body = JSON.parse(
      (
        (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
          .calls[0][1] as RequestInit
      ).body as string,
    );
    expect(body.organization_name).toBe("Town");
  });
});

describe("logout and token", () => {
  it("clears the token", async () => {
    mockFetchOnce({ access_token: "tok_x", user: { user_id: "u", email: "e", display_name: "d" } });
    await loginUser("e@example.com", "password123");
    expect(getAuthToken()).toBe("tok_x");
    logoutUser();
    expect(getAuthToken()).toBeNull();
  });
});

describe("getCurrentUser", () => {
  it("returns null without a token and does not call fetch", async () => {
    const spy = vi.fn();
    globalThis.fetch = spy;
    const user = await getCurrentUser();
    expect(user).toBeNull();
    expect(spy).not.toHaveBeenCalled();
  });

  it("attaches the Authorization header when signed in", async () => {
    // First store a token via login.
    mockFetchOnce({ access_token: "tok_auth", user: { user_id: "u", email: "e", display_name: "d" } });
    await loginUser("e@example.com", "password123");
    mockFetchOnce({
      user_id: "u",
      email: "e@example.com",
      display_name: "Signed In",
      is_active: true,
      is_demo_user: false,
    });
    const user = await getCurrentUser();
    expect(user?.displayName).toBe("Signed In");
    const headers = (
      (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
        .calls[0][1] as RequestInit
    ).headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer tok_auth");
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
