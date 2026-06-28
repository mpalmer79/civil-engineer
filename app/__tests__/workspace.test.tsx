import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const {
  isSignedIn,
  getCurrentUser,
  listMyOrganizations,
  listMyProjects,
} = vi.hoisted(() => ({
  isSignedIn: vi.fn(),
  getCurrentUser: vi.fn(),
  listMyOrganizations: vi.fn(),
  listMyProjects: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    isSignedIn: () => isSignedIn(),
    getCurrentUser: () => getCurrentUser(),
    listMyOrganizations: () => listMyOrganizations(),
    listMyProjects: () => listMyProjects(),
  };
});

import WorkspacePage from "@/app/workspace/page";
import WorkspaceSettingsPage from "@/app/workspace/settings/page";

beforeEach(() => {
  isSignedIn.mockReset();
  getCurrentUser.mockReset();
  listMyOrganizations.mockReset();
  listMyProjects.mockReset();
});

afterEach(() => cleanup());

describe("Workspace home", () => {
  it("prompts sign-in when signed out and keeps the demo reachable", async () => {
    isSignedIn.mockReturnValue(false);
    render(<WorkspacePage />);
    await waitFor(() => {
      expect(screen.getByText(/sign in to your workspace/i)).toBeInTheDocument();
    });
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).toContain("brookside meadows");
    expect(document.querySelector('a[href="/login"]')).not.toBeNull();
    expect(document.querySelector('a[href="/guided-demo"]')).not.toBeNull();
  });

  it("renders identity, project counts, and quick links when signed in", async () => {
    isSignedIn.mockReturnValue(true);
    getCurrentUser.mockResolvedValue({
      userId: "u1",
      email: "op@example.com",
      displayName: "Op Erator",
      isActive: true,
      isDemoUser: false,
      createdAt: null,
      lastLoginAt: null,
    });
    listMyOrganizations.mockResolvedValue([
      {
        organizationId: "o1",
        organizationName: "Meadow Civil",
        organizationType: "firm",
        sourceMode: "real",
        role: "org_admin",
        membershipId: "m1",
      },
    ]);
    listMyProjects.mockResolvedValue([
      {
        projectId: "p1",
        projectName: "Real Project",
        sourceMode: "real",
        visibilityMode: "controlled",
        demoPublic: false,
        organizationId: "o1",
        accessLevel: "reviewer",
      },
    ]);
    render(<WorkspacePage />);
    await waitFor(() => {
      expect(screen.getByText("Op Erator")).toBeInTheDocument();
    });
    expect(screen.getByText("Meadow Civil")).toBeInTheDocument();
    // Operator sees the pilot requests link.
    expect(document.querySelector('a[href="/admin/pilot-requests"]')).not.toBeNull();
    expect(document.querySelector('a[href="/projects"]')).not.toBeNull();
  });

  it("hides the pilot requests link for a non-operator", async () => {
    isSignedIn.mockReturnValue(true);
    getCurrentUser.mockResolvedValue({
      userId: "u2",
      email: "rev@example.com",
      displayName: "Rev Iewer",
      isActive: true,
      isDemoUser: false,
      createdAt: null,
      lastLoginAt: null,
    });
    listMyOrganizations.mockResolvedValue([]);
    listMyProjects.mockResolvedValue([]);
    render(<WorkspacePage />);
    await waitFor(() => {
      expect(screen.getByText("Rev Iewer")).toBeInTheDocument();
    });
    expect(document.querySelector('a[href="/admin/pilot-requests"]')).toBeNull();
  });

  it("states the design-partner pilot release posture", async () => {
    isSignedIn.mockReturnValue(false);
    render(<WorkspacePage />);
    await waitFor(() => {
      expect(screen.getByText(/release state: design-partner pilot/i)).toBeInTheDocument();
    });
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).toContain("billing is not active");
  });
});

describe("Workspace settings hub", () => {
  it("links to the active team, billing, and usage pages", () => {
    render(WorkspaceSettingsPage());
    expect(document.querySelector('a[href="/workspace/team"]')).not.toBeNull();
    expect(document.querySelector('a[href="/workspace/billing"]')).not.toBeNull();
    expect(document.querySelector('a[href="/workspace/usage"]')).not.toBeNull();
  });

  it("keeps remaining capabilities marked coming later", () => {
    render(WorkspaceSettingsPage());
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).toContain("coming later");
    // Billing is referenced but never claimed active.
    expect(text).toContain("billing");
    expect(text).not.toContain("billing is active");
    expect(text).not.toContain("subscription active");
  });
});
