import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Professional design pass coverage. These tests confirm the polished
// first-impression and deeper workflow pages render their structured cards,
// status chips, and empty states, and that no raw storage paths, secrets, or
// prohibited final-decision wording appear in the visible UI.

const refreshMock = vi.fn();
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
  notFound: () => {
    throw new Error("notFound");
  },
}));

const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "noncompliant",
  "passed review",
  "failed review",
  "design validated",
];

const ATTRIBUTION_TOKENS = [
  ["claude", "code"].join(" "),
  ["claude.ai", "code"].join("/"),
  ["co-authored", "by"].join("-"),
];

const FORBIDDEN_LEAKS = [
  "storage_path",
  "storage_key",
  "signed_url",
  "/var/",
  "/home/",
  ...ATTRIBUTION_TOKENS,
];

const {
  getCurrentUserMock,
  listMyOrganizationsMock,
  listMyProjectsMock,
  listProjectAccessMock,
  grantProjectAccessMock,
  isSignedInMock,
} = vi.hoisted(() => ({
  getCurrentUserMock: vi.fn(),
  listMyOrganizationsMock: vi.fn(),
  listMyProjectsMock: vi.fn(),
  listProjectAccessMock: vi.fn(),
  grantProjectAccessMock: vi.fn(),
  isSignedInMock: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getCurrentUser: getCurrentUserMock,
    listMyOrganizations: listMyOrganizationsMock,
    listMyProjects: listMyProjectsMock,
    listProjectAccess: listProjectAccessMock,
    grantProjectAccess: grantProjectAccessMock,
    isSignedIn: isSignedInMock,
  };
});

function assertSafe(container: HTMLElement) {
  const text = container.textContent?.toLowerCase() ?? "";
  for (const word of PROHIBITED_WORDS) {
    expect(text).not.toContain(word);
  }
  for (const leak of FORBIDDEN_LEAKS) {
    expect(text).not.toContain(leak);
  }
}

beforeEach(() => {
  globalThis.fetch = vi.fn().mockRejectedValue(new Error("no backend"));
  isSignedInMock.mockReturnValue(true);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Account page", () => {
  beforeEach(() => {
    getCurrentUserMock.mockResolvedValue({
      userId: "u1",
      email: "reviewer@example.com",
      displayName: "Reviewer One",
      isActive: true,
      isDemoUser: false,
      createdAt: null,
      lastLoginAt: null,
    });
    listMyOrganizationsMock.mockResolvedValue([
      {
        organizationId: "org_1",
        organizationName: "Town of Riverton",
        organizationType: "municipality",
        sourceMode: "user_created",
        role: "org_admin",
        membershipId: "m1",
      },
    ]);
    listMyProjectsMock.mockResolvedValue([
      {
        projectId: "proj_1",
        projectName: "Brookside Meadows",
        sourceMode: "user_created",
        visibilityMode: "private",
        demoPublic: false,
        organizationId: "org_1",
        accessLevel: "reviewer",
      },
    ]);
  });

  it("renders profile, organization, and project sections with chips", async () => {
    const { default: AccountPage } = await import("@/app/me/page");
    const { container } = render(<AccountPage />);
    await waitFor(() =>
      expect(screen.getByText("Town of Riverton")).toBeInTheDocument(),
    );
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Reviewer One")).toBeInTheDocument();
    expect(screen.getByText("Brookside Meadows")).toBeInTheDocument();
    // Role and access values are rendered as status chips with prefixes.
    expect(screen.getByText("org_admin")).toBeInTheDocument();
    expect(screen.getByText("reviewer")).toBeInTheDocument();
    assertSafe(container);
  });

  it("shows polished empty states when no orgs or projects exist", async () => {
    listMyOrganizationsMock.mockResolvedValue([]);
    listMyProjectsMock.mockResolvedValue([]);
    const { default: AccountPage } = await import("@/app/me/page");
    render(<AccountPage />);
    await waitFor(() =>
      expect(screen.getByText("No organizations yet")).toBeInTheDocument(),
    );
    expect(
      screen.getByText("No accessible projects yet"),
    ).toBeInTheDocument();
  });
});

describe("Project access page", () => {
  beforeEach(() => {
    listProjectAccessMock.mockResolvedValue([
      {
        projectAccessId: "pa_1",
        projectId: "proj_1",
        organizationId: null,
        userId: "u2",
        accessLevel: "reviewer",
        grantedByUserId: "u1",
        isActive: true,
        createdAt: null,
      },
    ]);
  });

  it("renders access entries as chips and a shared-styled grant form", async () => {
    const { default: ProjectAccessPage } = await import(
      "@/app/projects/[projectId]/access/page"
    );
    const { container } = render(
      <ProjectAccessPage params={{ projectId: "proj_1" }} />,
    );
    await waitFor(() =>
      expect(screen.getByText("Current access")).toBeInTheDocument(),
    );
    expect(screen.getByText("User u2")).toBeInTheDocument();
    // "reviewer" appears as the access chip label and as a select option.
    expect(screen.getAllByText("reviewer").length).toBeGreaterThan(0);
    // Grant form uses the shared form classes and a primary button.
    expect(screen.getByLabelText("User id")).toBeInTheDocument();
    expect(screen.getByLabelText("Access level")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Grant access" }),
    ).toBeInTheDocument();
    assertSafe(container);
  });
});
