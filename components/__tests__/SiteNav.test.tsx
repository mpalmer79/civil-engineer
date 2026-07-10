import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

// AccountNav and SiteNav read the current user and use the router. Keep them
// offline for these tests and control the session per test.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

const getCurrentUser = vi.fn(async (): Promise<unknown> => null);

vi.mock("@/lib/api", () => ({
  getCurrentUser: () => getCurrentUser(),
  logoutUser: vi.fn(),
}));

import SiteNav from "@/components/SiteNav";

afterEach(() => {
  cleanup();
  getCurrentUser.mockReset();
  getCurrentUser.mockResolvedValue(null);
});

describe("SiteNav public navigation", () => {
  it("shows only public product destinations when signed out", async () => {
    render(<SiteNav />);
    for (const label of ["Product", "Guided Demo", "Technical Overview", "Pilot"]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
    await waitFor(() =>
      expect(screen.getAllByText("Sign in").length).toBeGreaterThan(0),
    );
    // Operational workspace destinations stay hidden until sign-in.
    expect(screen.queryByText("Reviewer Queue")).toBeNull();
    expect(screen.queryByText("Organizations")).toBeNull();
    // The old flat demo modules menu no longer dominates the first impression.
    expect(screen.queryByText("Demo modules")).toBeNull();
  });

  it("renders the account/login control", async () => {
    render(<SiteNav />);
    await waitFor(() =>
      expect(screen.getAllByText("Sign in").length).toBeGreaterThan(0),
    );
  });

  it("exposes a mobile menu rather than hiding all navigation", () => {
    render(<SiteNav />);
    expect(screen.getAllByText("Menu").length).toBeGreaterThan(0);
  });
});

describe("SiteNav signed-in workspace navigation", () => {
  it("reveals the reviewer workspace destinations after sign-in", async () => {
    getCurrentUser.mockResolvedValue({
      userId: "user_test",
      email: "reviewer@example.com",
      displayName: "Test Reviewer",
      isActive: true,
      isDemoUser: false,
      createdAt: null,
      lastLoginAt: null,
    });
    render(<SiteNav />);
    await waitFor(() =>
      expect(screen.getAllByText("Workspace").length).toBeGreaterThan(0),
    );
    for (const label of [
      "Projects",
      "Dashboard",
      "Reviewer Queue",
      "Organizations",
      "Rule Packs",
    ]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
  });

  it("exposes disclosure controls that are keyboard focusable when signed in", async () => {
    getCurrentUser.mockResolvedValue({
      userId: "user_test",
      email: "reviewer@example.com",
      displayName: "Test Reviewer",
      isActive: true,
      isDemoUser: false,
      createdAt: null,
      lastLoginAt: null,
    });
    const { container } = render(<SiteNav />);
    await waitFor(() => {
      // Native summary elements are keyboard focusable disclosure controls and
      // carry the design-system focus ring from globals.css.
      expect(container.querySelectorAll("summary").length).toBeGreaterThan(0);
    });
  });
});
