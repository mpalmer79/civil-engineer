import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();
const refreshMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
}));

const mocks = vi.hoisted(() => ({
  isSignedIn: vi.fn(),
  listMyOrganizations: vi.fn(),
  listOrganizationMembers: vi.fn(),
  listInvitations: vi.fn(),
  createInvitation: vi.fn(),
  revokeInvitation: vi.fn(),
  getOrganizationBilling: vi.fn(),
  startCheckout: vi.fn(),
  getOrganizationUsage: vi.fn(),
  requestPasswordReset: vi.fn(),
  confirmPasswordReset: vi.fn(),
  lookupInvitation: vi.fn(),
  acceptInvitation: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, ...mocks };
});

import WorkspaceBillingClient from "@/components/WorkspaceBillingClient";
import WorkspaceUsageClient from "@/components/WorkspaceUsageClient";
import WorkspaceTeamClient from "@/components/WorkspaceTeamClient";
import PasswordResetRequestForm from "@/components/PasswordResetRequestForm";
import PasswordResetConfirmForm from "@/components/PasswordResetConfirmForm";
import AcceptInviteClient from "@/components/AcceptInviteClient";

const ADMIN_ORG = {
  organizationId: "o1",
  organizationName: "Acme Civil",
  organizationType: "consulting_engineer",
  sourceMode: "user_created",
  role: "org_admin",
  membershipId: "m1",
};

beforeEach(() => {
  for (const fn of Object.values(mocks)) fn.mockReset();
  mocks.isSignedIn.mockReturnValue(true);
  mocks.listMyOrganizations.mockResolvedValue([ADMIN_ORG]);
  mocks.listOrganizationMembers.mockResolvedValue([]);
  mocks.listInvitations.mockResolvedValue([]);
});

afterEach(() => cleanup());

// ---------------------------------------------------------------------------
// Billing
// ---------------------------------------------------------------------------

describe("WorkspaceBillingClient", () => {
  it("shows an honest inactive billing state and disables checkout", async () => {
    mocks.getOrganizationBilling.mockResolvedValue({
      subscription: {
        subscriptionId: "s1",
        organizationId: "o1",
        planCode: "demo",
        planName: "Demo",
        status: "inactive",
        currentPeriodEnd: null,
        limits: {},
      },
      billing: {
        enabled: false,
        mode: "inactive",
        message: "Billing is not active. No payment is collected.",
      },
      plans: [
        {
          planCode: "demo",
          name: "Demo",
          description: "Demo",
          priceDisplay: "Free",
          sortOrder: 0,
          limits: {},
        },
      ],
    });
    render(<WorkspaceBillingClient />);
    await waitFor(() =>
      expect(screen.getByText("Billing inactive")).toBeInTheDocument(),
    );
    const button = screen.getByText("Billing inactive") as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).toContain("not active");
    // Never claims an active subscription.
    expect(text).not.toContain("subscription active");
    expect(text).not.toContain("payment received");
  });
});

// ---------------------------------------------------------------------------
// Usage
// ---------------------------------------------------------------------------

describe("WorkspaceUsageClient", () => {
  it("renders advisory usage limits with status", async () => {
    mocks.getOrganizationUsage.mockResolvedValue({
      organizationId: "o1",
      planCode: "demo",
      planName: "Demo",
      subscriptionStatus: "inactive",
      enforcement: "advisory",
      limits: [
        { key: "projects", category: "project_created", used: 1, limit: 1, status: "over" },
        { key: "documents", category: "document_uploaded", used: 0, limit: 5, status: "ok" },
      ],
      totals: { project_created: 1 },
    });
    render(<WorkspaceUsageClient />);
    await waitFor(() => expect(screen.getByText("Projects")).toBeInTheDocument());
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).toContain("advisory");
    expect(text).toContain("not blocked");
  });
});

// ---------------------------------------------------------------------------
// Team
// ---------------------------------------------------------------------------

describe("WorkspaceTeamClient", () => {
  it("lets an admin send an invitation", async () => {
    mocks.createInvitation.mockResolvedValue({
      ok: true,
      backendReachable: true,
      data: {
        invitation: {
          invitationId: "inv1",
          organizationId: "o1",
          email: "t@example.com",
          role: "reviewer",
          status: "pending",
          invitedByUserId: null,
          acceptedByUserId: null,
          expiresAt: null,
          acceptedAt: null,
          revokedAt: null,
          createdAt: null,
        },
        devInviteToken: "devtoken123",
        emailSent: false,
      },
    });
    render(<WorkspaceTeamClient />);
    await waitFor(() =>
      expect(screen.getByText("Invite a teammate")).toBeInTheDocument(),
    );
    fireEvent.change(screen.getByPlaceholderText("teammate@example.com"), {
      target: { value: "t@example.com" },
    });
    fireEvent.click(screen.getByText("Send invite"));
    await waitFor(() => expect(mocks.createInvitation).toHaveBeenCalled());
    expect(mocks.createInvitation).toHaveBeenCalledWith("o1", {
      email: "t@example.com",
      role: "reviewer",
    });
  });

  it("hides the invite form for a non-admin member", async () => {
    mocks.listMyOrganizations.mockResolvedValue([
      { ...ADMIN_ORG, role: "reviewer" },
    ]);
    render(<WorkspaceTeamClient />);
    await waitFor(() =>
      expect(screen.getByText("Team management")).toBeInTheDocument(),
    );
    expect(screen.queryByText("Invite a teammate")).toBeNull();
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).toContain("requires an organization admin");
  });
});

// ---------------------------------------------------------------------------
// Password reset
// ---------------------------------------------------------------------------

describe("Password reset", () => {
  it("shows a uniform message and a dev link on request", async () => {
    mocks.requestPasswordReset.mockResolvedValue({
      ok: true,
      backendReachable: true,
      data: {
        detail: "If an account exists for that email, a link has been issued.",
        devResetToken: "reset123",
      },
    });
    render(<PasswordResetRequestForm />);
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), {
      target: { value: "a@example.com" },
    });
    fireEvent.click(screen.getByText("Send reset link"));
    await waitFor(() => expect(mocks.requestPasswordReset).toHaveBeenCalled());
    expect(
      document.querySelector('a[href*="/reset-password/confirm?token="]'),
    ).not.toBeNull();
  });

  it("rejects a missing token on the confirm form", () => {
    render(<PasswordResetConfirmForm token="" />);
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).toContain("missing its token");
  });

  it("submits a new password with a valid token", async () => {
    mocks.confirmPasswordReset.mockResolvedValue({
      ok: true,
      backendReachable: true,
      data: { detail: "ok" },
    });
    render(<PasswordResetConfirmForm token="tok1" />);
    const inputs = document.querySelectorAll('input[type="password"]');
    fireEvent.change(inputs[0], { target: { value: "newpassword1" } });
    fireEvent.change(inputs[1], { target: { value: "newpassword1" } });
    fireEvent.click(screen.getByText("Set new password"));
    await waitFor(() =>
      expect(mocks.confirmPasswordReset).toHaveBeenCalledWith(
        "tok1",
        "newpassword1",
      ),
    );
  });
});

// ---------------------------------------------------------------------------
// Accept invite
// ---------------------------------------------------------------------------

describe("AcceptInviteClient", () => {
  it("previews the invitation and accepts when signed in", async () => {
    mocks.isSignedIn.mockReturnValue(true);
    mocks.lookupInvitation.mockResolvedValue({
      organizationId: "o1",
      organizationName: "Acme Civil",
      email: "t@example.com",
      role: "reviewer",
      status: "pending",
      acceptable: true,
      expiresAt: null,
    });
    mocks.acceptInvitation.mockResolvedValue({
      ok: true,
      backendReachable: true,
      data: { organizationId: "o1", role: "reviewer", detail: "You have joined Acme Civil." },
    });
    render(<AcceptInviteClient token="invtok" />);
    await waitFor(() =>
      expect(screen.getByText("Accept invitation")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByText("Accept invitation"));
    await waitFor(() => expect(mocks.acceptInvitation).toHaveBeenCalledWith("invtok"));
  });

  it("prompts sign-in when signed out", async () => {
    mocks.isSignedIn.mockReturnValue(false);
    mocks.lookupInvitation.mockResolvedValue({
      organizationId: "o1",
      organizationName: "Acme Civil",
      email: "t@example.com",
      role: "reviewer",
      status: "pending",
      acceptable: true,
      expiresAt: null,
    });
    render(<AcceptInviteClient token="invtok" />);
    await waitFor(() =>
      expect(document.querySelector('a[href="/login"]')).not.toBeNull(),
    );
    expect(screen.queryByText("Accept invitation")).toBeNull();
  });

  it("shows an unusable state for an expired invitation", async () => {
    mocks.isSignedIn.mockReturnValue(true);
    mocks.lookupInvitation.mockResolvedValue({
      organizationId: "o1",
      organizationName: "Acme Civil",
      email: "t@example.com",
      role: "reviewer",
      status: "expired",
      acceptable: false,
      expiresAt: null,
    });
    render(<AcceptInviteClient token="invtok" />);
    await waitFor(() => {
      const text = (document.body.textContent ?? "").toLowerCase();
      expect(text).toContain("can no longer be accepted");
    });
  });
});
