import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import BackendStatusBanner from "@/components/BackendStatusBanner";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

describe("BackendStatusBanner", () => {
  it("flags a missing backend URL when the env var is unset and fetch fails", async () => {
    // NEXT_PUBLIC_API_BASE_URL is not set in the test environment, so a failed
    // connection is most likely a missing backend URL rather than a down
    // backend.
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("down"));
    render(<BackendStatusBanner />);
    await waitFor(() =>
      expect(screen.getByText(/Backend URL is not set/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/NEXT_PUBLIC_API_BASE_URL/)).toBeInTheDocument();
  });

  it("reports an unreachable backend when the URL is set but fetch fails", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://backend.example.com");
    vi.resetModules();
    const { default: Banner } = await import("@/components/BackendStatusBanner");
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("down"));
    render(<Banner />);
    await waitFor(() =>
      expect(screen.getByText(/is not reachable/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/may not be/i)).toBeInTheDocument();
  });

  it("distinguishes a 404 on /health when the API routes still respond", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 404 } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ project_id: "proj_brookside_meadows" }),
      } as Response);
    render(<BackendStatusBanner />);
    await waitFor(() =>
      expect(screen.getByText(/\/health returned 404/i)).toBeInTheDocument(),
    );
  });

  it("flags a likely wrong API prefix when neither route responds", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 404 } as Response)
      .mockResolvedValueOnce({ ok: false, status: 404 } as Response);
    render(<BackendStatusBanner />);
    await waitFor(() =>
      expect(screen.getByText(/API prefix/i)).toBeInTheDocument(),
    );
  });

  it("shows a connected message when the backend health check succeeds", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: "ok", version: "1.0.0" }),
    } as Response);
    render(<BackendStatusBanner />);
    await waitFor(() =>
      expect(screen.getByText(/Backend connected/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/version 1.0.0/)).toBeInTheDocument();
  });
});
