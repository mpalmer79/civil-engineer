import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

// AccountNav (rendered inside SiteNav) reads the current user and uses the
// router. Keep it offline and signed out for these tests.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("@/lib/api", () => ({
  getCurrentUser: vi.fn(async () => null),
  logoutUser: vi.fn(),
}));

import SiteNav from "@/components/SiteNav";

afterEach(() => cleanup());

describe("SiteNav primary navigation", () => {
  it("includes the primary product links", () => {
    render(<SiteNav />);
    for (const label of [
      "Projects",
      "Rule Packs",
      "Organizations",
      "Guided Demo",
    ]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
  });

  it("renders the account/login control", async () => {
    render(<SiteNav />);
    // AccountNav resolves to a Sign in link when signed out.
    await waitFor(() =>
      expect(screen.getAllByText("Sign in").length).toBeGreaterThan(0),
    );
  });

  it("keeps the older Brookside Meadows demo routes discoverable via the demo menu", () => {
    render(<SiteNav />);
    // The grouped demo modules disclosure exposes the older routes.
    expect(screen.getAllByText("Demo modules").length).toBeGreaterThan(0);
    for (const label of [
      "Project Dashboard",
      "CAD Intake",
      "Workflow Board",
      "Audit",
      "Evaluation",
    ]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
  });

  it("exposes a mobile menu rather than hiding all navigation", () => {
    render(<SiteNav />);
    expect(screen.getAllByText("Menu").length).toBeGreaterThan(0);
  });

  it("does not surface Sprint 9 dashboard routes that do not exist yet", () => {
    render(<SiteNav />);
    expect(screen.queryByText("Dashboard")).toBeNull();
    expect(screen.queryByText("Reviewer Queue")).toBeNull();
  });
});
