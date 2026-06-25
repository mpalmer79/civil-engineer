import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import BackendStatusBanner from "@/components/BackendStatusBanner";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("BackendStatusBanner", () => {
  it("shows a helpful message when the backend is unavailable", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("down"));
    render(<BackendStatusBanner />);
    await waitFor(() =>
      expect(screen.getByText(/not reachable/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/NEXT_PUBLIC_API_BASE_URL/)).toBeInTheDocument();
  });

  it("shows a connected message when the backend health check succeeds", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok", version: "1.0.0" }),
    } as Response);
    render(<BackendStatusBanner />);
    await waitFor(() =>
      expect(screen.getByText(/Backend connected/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/version 1.0.0/)).toBeInTheDocument();
  });
});
