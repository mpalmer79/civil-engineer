import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const trackDemoEvent = vi.fn();
vi.mock("@/lib/analytics", () => ({
  trackDemoEvent: (...args: unknown[]) => trackDemoEvent(...args),
}));

const {
  listPilotRequests,
  updatePilotRequestStatus,
  updatePilotRequestNotes,
  exportPilotRequestsCsv,
} = vi.hoisted(() => ({
  listPilotRequests: vi.fn(),
  updatePilotRequestStatus: vi.fn(),
  updatePilotRequestNotes: vi.fn(),
  exportPilotRequestsCsv: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    listPilotRequests: () => listPilotRequests(),
    updatePilotRequestStatus: (...a: unknown[]) => updatePilotRequestStatus(...a),
    updatePilotRequestNotes: (...a: unknown[]) => updatePilotRequestNotes(...a),
    exportPilotRequestsCsv: () => exportPilotRequestsCsv(),
  };
});

import PilotRequestsAdminPage from "@/app/admin/pilot-requests/page";

function record(overrides = {}) {
  return {
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
    status: "new",
    internalNotes: null,
    lastContactedAt: null,
    createdAt: "2026-06-28T00:00:00Z",
    updatedAt: "2026-06-28T00:00:00Z",
    ...overrides,
  };
}

beforeEach(() => {
  trackDemoEvent.mockReset();
  listPilotRequests.mockReset();
  updatePilotRequestStatus.mockReset();
  updatePilotRequestNotes.mockReset();
  exportPilotRequestsCsv.mockReset();
});

afterEach(() => cleanup());

describe("Pilot requests admin access states", () => {
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

  it("degrades honestly when the backend is unreachable", async () => {
    listPilotRequests.mockResolvedValue({ status: "unreachable" });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByText(/backend unavailable/i)).toBeInTheDocument();
    });
  });

  it("fires pilot_admin_viewed on mount", async () => {
    listPilotRequests.mockResolvedValue({ status: "ok", data: [] });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByText(/no pilot requests yet/i)).toBeInTheDocument();
    });
    expect(trackDemoEvent.mock.calls.map((c) => c[0])).toContain("pilot_admin_viewed");
  });
});

describe("Pilot requests admin operations", () => {
  it("renders requests with their operator status", async () => {
    listPilotRequests.mockResolvedValue({
      status: "ok",
      data: [record({ status: "contacted" })],
    });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByTestId("pilot-request-list")).toBeInTheDocument();
    });
    expect(screen.getByText("Meadow Civil Group")).toBeInTheDocument();
    expect(screen.getAllByText(/contacted/i).length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/internal notes for/i)).toBeInTheDocument();
  });

  it("filters the list by status", async () => {
    listPilotRequests.mockResolvedValue({
      status: "ok",
      data: [
        record({ pilotRequestId: "p1", firmName: "Alpha Civil", status: "new" }),
        record({ pilotRequestId: "p2", firmName: "Beta Civil", status: "qualified" }),
      ],
    });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByText("Alpha Civil")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/filter by status/i), {
      target: { value: "qualified" },
    });
    expect(screen.queryByText("Alpha Civil")).toBeNull();
    expect(screen.getByText("Beta Civil")).toBeInTheDocument();
  });

  it("updates a request status and reports success", async () => {
    listPilotRequests.mockResolvedValue({ status: "ok", data: [record()] });
    updatePilotRequestStatus.mockResolvedValue({
      status: "ok",
      data: record({ status: "qualified" }),
    });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByTestId("pilot-request-list")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/status for meadow civil group/i), {
      target: { value: "qualified" },
    });
    await waitFor(() => {
      expect(screen.getByText(/status saved/i)).toBeInTheDocument();
    });
    expect(updatePilotRequestStatus).toHaveBeenCalledWith("pilot_abc", "qualified", true);
    expect(trackDemoEvent.mock.calls.map((c) => c[0])).toContain(
      "pilot_request_status_changed",
    );
  });

  it("saves internal notes and reports success", async () => {
    listPilotRequests.mockResolvedValue({ status: "ok", data: [record()] });
    updatePilotRequestNotes.mockResolvedValue({
      status: "ok",
      data: record({ internalNotes: "Called, will follow up" }),
    });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByTestId("pilot-request-list")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/internal notes for/i), {
      target: { value: "Called, will follow up" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save notes/i }));
    await waitFor(() => {
      expect(screen.getByText(/notes saved/i)).toBeInTheDocument();
    });
    expect(trackDemoEvent.mock.calls.map((c) => c[0])).toContain(
      "pilot_request_note_saved",
    );
  });

  it("exposes a protected CSV export control that calls the gated API", async () => {
    listPilotRequests.mockResolvedValue({ status: "ok", data: [record()] });
    exportPilotRequestsCsv.mockResolvedValue({
      status: "ok",
      csv: "created_at,status,full_name\n",
    });
    render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByTestId("pilot-request-list")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /export csv/i }));
    await waitFor(() => {
      expect(exportPilotRequestsCsv).toHaveBeenCalled();
    });
    expect(trackDemoEvent.mock.calls.map((c) => c[0])).toContain(
      "pilot_request_exported",
    );
  });

  it("never exposes a file-upload control", async () => {
    listPilotRequests.mockResolvedValue({ status: "ok", data: [record()] });
    const { container } = render(<PilotRequestsAdminPage />);
    await waitFor(() => {
      expect(screen.getByTestId("pilot-request-list")).toBeInTheDocument();
    });
    expect(container.querySelector('input[type="file"]')).toBeNull();
  });
});
