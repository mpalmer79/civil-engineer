import { existsSync } from "node:fs";
import { join } from "node:path";

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Affirmative final-decision wording that must never appear as a product promise,
// badge, CTA, or conclusion on the pilot page. Negative boundary statements
// ("does not approve ... certify ... verify ... validate") are allowed.
const PROHIBITED_PROMISES = [
  "plan approved",
  "design validated",
  "fully compliant",
  "passes review",
  "passed review",
  "guaranteed compliance",
  "meets all requirements",
  "marked safe",
];

const trackDemoEvent = vi.fn();
vi.mock("@/lib/analytics", () => ({
  trackDemoEvent: (...args: unknown[]) => trackDemoEvent(...args),
}));

const submitPilotRequest = vi.fn();
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    submitPilotRequest: (...a: unknown[]) => submitPilotRequest(...a),
  };
});

import PilotPage from "@/app/pilot/page";

const SAMPLE = {
  name: "Dana Civil",
  email: "dana@example.com",
  firm: "Meadow Civil Group",
  role: "Project Engineer",
  pain: "Avoidable resubmittal cycles",
};

function fillRequiredFields() {
  fireEvent.change(screen.getByLabelText(/full name/i), {
    target: { value: SAMPLE.name },
  });
  fireEvent.change(screen.getByLabelText(/work email/i), {
    target: { value: SAMPLE.email },
  });
  fireEvent.change(screen.getByLabelText(/firm \/ company name/i), {
    target: { value: SAMPLE.firm },
  });
  fireEvent.change(screen.getByLabelText(/role or title/i), {
    target: { value: SAMPLE.role },
  });
  fireEvent.change(screen.getByLabelText(/project type/i), {
    target: { value: "Residential subdivision" },
  });
  fireEvent.change(screen.getByLabelText(/interest level/i), {
    target: { value: "evaluating" },
  });
  fireEvent.change(screen.getByLabelText(/primary pain/i), {
    target: { value: SAMPLE.pain },
  });
}

beforeEach(() => {
  trackDemoEvent.mockReset();
  submitPilotRequest.mockReset();
  submitPilotRequest.mockResolvedValue({
    ok: true,
    backendReachable: true,
    data: {
      pilotRequestId: "pilot_test123",
      received: true,
      message: "Thanks. Your pilot request was received.",
    },
  });
});

afterEach(() => cleanup());

describe("Pilot route", () => {
  it("exists as a real Next.js route directory", () => {
    expect(existsSync(join(process.cwd(), "app/pilot"))).toBe(true);
  });

  it("renders the design-partner pilot page", () => {
    render(PilotPage());
    expect(
      screen.getByRole("heading", { name: /start a design-partner pilot/i }),
    ).toBeInTheDocument();
  });

  it("renders all required pilot form fields", () => {
    render(PilotPage());
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/work email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/firm \/ company name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/role or title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/project type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/interest level/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/primary pain/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/sample dxf/i)).toBeInTheDocument();
  });
});

describe("Pilot form submission", () => {
  it("blocks submission and shows an error when required fields are empty", () => {
    render(PilotPage());
    fireEvent.click(
      screen.getByRole("button", { name: /request design-partner access/i }),
    );
    expect(screen.getByText(/complete the required fields/i)).toBeInTheDocument();
    expect(submitPilotRequest).not.toHaveBeenCalled();
  });

  it("shows an honest success state after a successful submission", async () => {
    render(PilotPage());
    fillRequiredFields();
    fireEvent.click(
      screen.getByRole("button", { name: /request design-partner access/i }),
    );
    await waitFor(() => {
      expect(screen.getByTestId("pilot-success")).toBeInTheDocument();
    });
    expect(submitPilotRequest).toHaveBeenCalledTimes(1);
    expect(
      screen.getByText(/your pilot request was received/i),
    ).toBeInTheDocument();
  });

  it("surfaces an error and stays on the form when submission fails", async () => {
    submitPilotRequest.mockResolvedValue({
      ok: false,
      backendReachable: false,
      error: "We could not reach the server to record your request.",
    });
    render(PilotPage());
    fillRequiredFields();
    fireEvent.click(
      screen.getByRole("button", { name: /request design-partner access/i }),
    );
    await waitFor(() => {
      expect(screen.getByText(/could not reach the server/i)).toBeInTheDocument();
    });
    expect(screen.queryByTestId("pilot-success")).toBeNull();
  });
});

describe("Pilot analytics", () => {
  it("fires pilot form analytics events without sensitive field values", async () => {
    render(PilotPage());
    fireEvent.focus(screen.getByLabelText(/full name/i));
    fillRequiredFields();
    fireEvent.click(
      screen.getByRole("button", { name: /request design-partner access/i }),
    );
    await waitFor(() => {
      expect(screen.getByTestId("pilot-success")).toBeInTheDocument();
    });

    const events = trackDemoEvent.mock.calls.map((c) => c[0]);
    expect(events).toContain("pilot_form_started");
    expect(events).toContain("pilot_form_submitted");

    // No call may carry the entered name, email, firm, or free-text pain.
    const serialized = JSON.stringify(trackDemoEvent.mock.calls).toLowerCase();
    expect(serialized).not.toContain(SAMPLE.email.toLowerCase());
    expect(serialized).not.toContain(SAMPLE.name.toLowerCase());
    expect(serialized).not.toContain(SAMPLE.firm.toLowerCase());
    expect(serialized).not.toContain(SAMPLE.pain.toLowerCase());
  });

  it("fires pilot_form_error on a validation failure", () => {
    render(PilotPage());
    fireEvent.click(
      screen.getByRole("button", { name: /request design-partner access/i }),
    );
    const events = trackDemoEvent.mock.calls.map((c) => c[0]);
    expect(events).toContain("pilot_form_error");
  });
});

describe("Pilot page language hygiene", () => {
  it("keeps the pilot copy AEC/pre-submittal focused", () => {
    const { container } = render(PilotPage());
    const text = (container.textContent ?? "").toLowerCase();
    expect(text).toContain("pre-submittal qa");
    expect(text).toContain("review-support");
    expect(text).toContain("design partner");
  });

  it("does not use prohibited final-decision wording as a product promise", () => {
    const { container } = render(PilotPage());
    const text = (container.textContent ?? "").toLowerCase();
    for (const phrase of PROHIBITED_PROMISES) {
      expect(text).not.toContain(phrase);
    }
  });
});
