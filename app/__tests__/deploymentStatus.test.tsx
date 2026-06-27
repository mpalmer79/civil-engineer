import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Keep the page offline and deterministic. Provide safe readiness and storage
// diagnostics; keep API_BASE_URL and everything else real.
const readiness = {
  status: "ready",
  service: "Civil Engineer AI Backend",
  version: "1.0.0",
  demoMode: true,
  checks: [
    { category: "database", status: "ready", message: "Database responded." },
    {
      category: "authentication",
      status: "configured",
      message: "Auth secret configured.",
    },
    { category: "storage", status: "ready", message: "Storage configured." },
  ],
};

const storage = {
  provider: "local",
  configured: true,
  status: "ready",
  message: "Local development storage is selected.",
  items: [],
};

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getReadiness: vi.fn(async () => readiness),
    getStorageDiagnostics: vi.fn(async () => storage),
  };
});

import DeploymentStatusPage from "@/app/deployment-status/page";

beforeEach(() => {
  // BackendStatusBanner fetches /health; keep it from making a real request.
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ version: "1.0.0" }),
  } as Response);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("DeploymentStatusPage", () => {
  it("renders the deployment status heading and sections", async () => {
    render(<DeploymentStatusPage />);
    expect(
      screen.getByRole("heading", { name: "Deployment status" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Frontend configuration")).toBeInTheDocument();
    expect(screen.getByText("Backend readiness")).toBeInTheDocument();
    expect(screen.getByText("Storage status")).toBeInTheDocument();
    expect(screen.getByText("Troubleshooting guidance")).toBeInTheDocument();
  });

  it("shows readiness and storage status once loaded", async () => {
    render(<DeploymentStatusPage />);
    await waitFor(() =>
      expect(screen.getByText(/Provider local/i)).toBeInTheDocument(),
    );
    // Readiness check categories appear.
    expect(screen.getByText("database")).toBeInTheDocument();
    expect(screen.getByText("storage")).toBeInTheDocument();
    // Safe status labels are shown.
    expect(screen.getAllByTestId("status-badge").length).toBeGreaterThan(0);
  });

  it("shows the public backend origin and frontend env guidance", async () => {
    render(<DeploymentStatusPage />);
    expect(screen.getByTestId("backend-origin")).toBeInTheDocument();
    expect(
      screen.getByText(/NEXT_PUBLIC_API_BASE_URL must be the backend origin only/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Do not include \/api\/v1 in NEXT_PUBLIC_API_BASE_URL/i),
    ).toBeInTheDocument();
  });

  it("does not expose secrets, tokens, or raw paths in visible UI", async () => {
    const { container } = render(<DeploymentStatusPage />);
    await waitFor(() =>
      expect(screen.getByText(/Provider local/i)).toBeInTheDocument(),
    );
    const text = (container.textContent ?? "").toLowerCase();
    // Look for value-shaped leaks, not descriptive prose. The page may mention
    // that it shows "no secrets"; it must never render an actual secret value,
    // token, credential, database URL, or raw file system path.
    for (const bad of [
      "bearer ey",
      "sqlite:///",
      "/home/",
      "akia",
      "password=",
      "secret_access_key=",
      "-----begin",
    ]) {
      expect(text).not.toContain(bad);
    }
  });

  it("uses no prohibited final-decision wording", async () => {
    const { container } = render(<DeploymentStatusPage />);
    const text = (container.textContent ?? "").toLowerCase();
    for (const phrase of [
      "plan approved",
      "deployment certified",
      "compliance verified",
      "safe deployment",
      "passed review",
      "final approval",
    ]) {
      expect(text).not.toContain(phrase);
    }
  });
});
