import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import BackendStatusBanner from "@/components/BackendStatusBanner";

afterEach(() => {
  vi.restoreAllMocks();
});

// In the test environment NEXT_PUBLIC_API_BASE_URL is not set, so the base URL is
// the local default. That means a network failure surfaces as the "URL not set"
// guidance rather than a generic "unreachable" message.

describe("BackendStatusBanner", () => {
  it("flags a missing backend URL when the default is used and the fetch fails", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("down"));
    render(<BackendStatusBanner />);
    await waitFor(() =>
      expect(screen.getByText(/Backend URL is not set/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/NEXT_PUBLIC_API_BASE_URL/)).toBeInTheDocument();
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

  it("explains a 404 on the health route as a likely prefix or base URL issue", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({}),
    } as Response);
    render(<BackendStatusBanner />);
    await waitFor(() =>
      expect(screen.getByText(/\/health returned 404/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/without\s+\/api\/v1/i)).toBeInTheDocument();
  });
});
