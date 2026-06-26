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
  notFound: () => {
    throw new Error("notFound");
  },
}));

const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "compliant",
  "verified",
  "passed review",
  "resolved",
  "closed",
];

const {
  loginMock,
  registerMock,
  getCurrentUserMock,
  isSignedInMock,
  logoutMock,
} = vi.hoisted(() => ({
  loginMock: vi.fn(),
  registerMock: vi.fn(),
  getCurrentUserMock: vi.fn(),
  isSignedInMock: vi.fn(),
  logoutMock: vi.fn(),
}));

beforeEach(() => {
  loginMock.mockReset();
  registerMock.mockReset();
  getCurrentUserMock.mockReset();
  isSignedInMock.mockReset();
  logoutMock.mockReset();
  loginMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: { token: "tok", user: { displayName: "Demo Reviewer" } },
  });
  registerMock.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: { token: "tok", user: { displayName: "New" } },
  });
  getCurrentUserMock.mockResolvedValue(null);
  isSignedInMock.mockReturnValue(false);
});

afterEach(() => {
  cleanup();
  pushMock.mockReset();
  refreshMock.mockReset();
});

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    loginUser: loginMock,
    registerUser: registerMock,
    getCurrentUser: getCurrentUserMock,
    isSignedIn: isSignedInMock,
    logoutUser: logoutMock,
    listMyOrganizations: vi.fn(async () => []),
    listMyProjects: vi.fn(async () => []),
  };
});

import LoginForm from "@/components/LoginForm";
import RegisterForm from "@/components/RegisterForm";
import PermissionDeniedCard from "@/components/PermissionDeniedCard";
import AccountNav from "@/components/AccountNav";
import SignInNotice from "@/components/SignInNotice";
import LoginPage from "@/app/login/page";
import RegisterPage from "@/app/register/page";
import AccountPage from "@/app/me/page";

describe("Login page and form", () => {
  it("renders the login form", () => {
    render(<LoginPage />);
    expect(
      screen.getByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("reviewer@example.com"),
    ).toBeInTheDocument();
  });

  it("submits the expected credentials", async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByPlaceholderText("reviewer@example.com"), {
      target: { value: "reviewer@example.com" },
    });
    const password = document.querySelector(
      'input[type="password"]',
    ) as HTMLInputElement;
    fireEvent.change(password, { target: { value: "password123" } });
    fireEvent.click(screen.getByText("Sign in"));
    await waitFor(() => expect(loginMock).toHaveBeenCalled());
    expect(loginMock.mock.calls[0][0]).toBe("reviewer@example.com");
    expect(loginMock.mock.calls[0][1]).toBe("password123");
  });
});

describe("Register page", () => {
  it("renders the register form", () => {
    render(<RegisterPage />);
    expect(screen.getByText("Create an account")).toBeInTheDocument();
    expect(screen.getByText("Create account")).toBeInTheDocument();
  });

  it("submits registration with a display name", async () => {
    render(<RegisterForm />);
    const inputs = document.querySelectorAll("input");
    fireEvent.change(inputs[0], { target: { value: "New Reviewer" } });
    fireEvent.change(inputs[1], { target: { value: "new@example.com" } });
    fireEvent.change(inputs[2], { target: { value: "password123" } });
    fireEvent.click(screen.getByText("Create account"));
    await waitFor(() => expect(registerMock).toHaveBeenCalled());
    expect(registerMock.mock.calls[0][0].email).toBe("new@example.com");
  });
});

describe("PermissionDeniedCard", () => {
  it("renders the default review-support message", () => {
    render(<PermissionDeniedCard />);
    expect(screen.getByText("Permission denied")).toBeInTheDocument();
    expect(
      screen.getByText(/Ask a project admin or organization admin/i),
    ).toBeInTheDocument();
  });
});

describe("AccountNav", () => {
  it("shows a sign-in link when signed out", async () => {
    getCurrentUserMock.mockResolvedValue(null);
    render(<AccountNav />);
    await waitFor(() => expect(screen.getByText("Sign in")).toBeInTheDocument());
  });

  it("shows the user name and sign out when signed in", async () => {
    getCurrentUserMock.mockResolvedValue({
      userId: "u",
      email: "e@example.com",
      displayName: "Jordan Reviewer",
      isActive: true,
      isDemoUser: false,
      createdAt: null,
      lastLoginAt: null,
    });
    render(<AccountNav />);
    await waitFor(() =>
      expect(screen.getByText("Jordan Reviewer")).toBeInTheDocument(),
    );
    expect(screen.getByText("Sign out")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Sign out"));
    expect(logoutMock).toHaveBeenCalled();
  });
});

describe("SignInNotice", () => {
  it("prompts to sign in when signed out", async () => {
    isSignedInMock.mockReturnValue(false);
    render(<SignInNotice />);
    await waitFor(() =>
      expect(screen.getByText("Sign in")).toBeInTheDocument(),
    );
  });

  it("renders nothing when signed in", async () => {
    isSignedInMock.mockReturnValue(true);
    const { container } = render(<SignInNotice />);
    await waitFor(() => expect(container.textContent).toBe(""));
  });
});

describe("Account page", () => {
  it("shows a not-signed-in message when signed out", async () => {
    getCurrentUserMock.mockResolvedValue(null);
    render(<AccountPage />);
    await waitFor(() =>
      expect(screen.getByText("Not signed in")).toBeInTheDocument(),
    );
  });
});

describe("Professional boundary in new Sprint 5 UI", () => {
  it("uses no prohibited final-decision wording", async () => {
    const { container: c1 } = render(<LoginPage />);
    const { container: c2 } = render(<RegisterPage />);
    const { container: c3 } = render(<PermissionDeniedCard />);
    const text = (
      (c1.textContent ?? "") +
      (c2.textContent ?? "") +
      (c3.textContent ?? "")
    ).toLowerCase();
    for (const word of PROHIBITED_WORDS) {
      expect(text).not.toContain(word);
    }
  });

  it("shows no password value in the rendered login DOM", () => {
    const { container } = render(<LoginForm />);
    // The password input exists but carries no seeded value.
    const password = container.querySelector(
      'input[type="password"]',
    ) as HTMLInputElement;
    expect(password.value).toBe("");
  });
});
