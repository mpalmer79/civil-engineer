import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { listPilotRequests } = vi.hoisted(() => ({
  listPilotRequests: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    listPilotRequests: () => listPilotRequests(),
  };
});

import PilotRequestsAdminPage from "@/app/admin/pilot-requests/page";

const SAMPLE = {
  pilotRequestId: "pilot_abc",
  fullName: "Dana Civil",
  workEmail: "dana@example.com",
  firmName: "Meadow Civil Group",
  roleTitle: "Project Engineer",
  projectType: "Residential subdivision",
  primaryPain: "Avoidable resubmittal cycles",
  interestLevel: "evaluating",
  notes: "Saw the demo",
  hasSamplePackage: true,
  createdAt: "2026-06-28T00:00:00Z",
};

beforeEach(() => {
  listPilotRequests.mockReset();
});

afterEach(() => cleanup());

describe("Pilot requests admin view", () => {
  it("shows a sign-in state to anonymous (unauthorized) visitors", async () => {
    listPilotRequests.mockResolvedValue({ status: "unauthorized" });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByText(/sign in required/i)).toBeInTheDocument();
    });
    expect(screen.queryByTestId("pilot-request-list")).toBeNull();
  });

  it("shows an operator-access state to a non-admin (forbidden) user", async () => {
    listPilotRequests.mockResolvedValue({ status: "forbidden" });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByText(/operator access required/i)).toBeInTheDocument();
    });
    expect(screen.queryByTestId("pilot-request-list")).toBeNull();
  });

  it("renders submitted requests for an authorized operator", async () => {
    listPilotRequests.mockResolvedValue({ status: "ok", data: [SAMPLE] });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByTestId("pilot-request-list")).toBeInTheDocument();
    });
    expect(screen.getByText("Meadow Civil Group")).toBeInTheDocument();
    expect(screen.getByText("dana@example.com")).toBeInTheDocument();
    expect(screen.getByText(/avoidable resubmittal cycles/i)).toBeInTheDocument();
  });

  it("renders an empty state when there are no requests", async () => {
    listPilotRequests.mockResolvedValue({ status: "ok", data: [] });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByText(/no pilot requests yet/i)).toBeInTheDocument();
    });
    expect(screen.queryByTestId("pilot-request-list")).toBeNull();
  });

  it("degrades honestly when the backend is unreachable", async () => {
    listPilotRequests.mockResolvedValue({ status: "unreachable" });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByText(/backend unavailable/i)).toBeInTheDocument();
    });
    expect(screen.queryByTestId("pilot-request-list")).toBeNull();
  });

  it("never exposes a file-upload control", async () => {
    listPilotRequests.mockResolvedValue({ status: "ok", data: [SAMPLE] });
    const { container } = render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByTestId("pilot-request-list")).toBeInTheDocument();
    });
    expect(container.querySelector('input[type="file"]')).toBeNull();
  });
});
