import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import StatusChip, { humanizeStatus } from "@/components/StatusChip";

afterEach(() => cleanup());

describe("StatusChip", () => {
  it("renders the label inside a design-system chip", () => {
    render(<StatusChip label="Intake started" />);
    const chip = screen.getByText("Intake started");
    expect(chip).toHaveClass("chip");
    expect(chip).toHaveClass("chip-neutral");
  });

  it("applies the requested tone variant", () => {
    render(<StatusChip label="Waiting" tone="warning" />);
    expect(screen.getByText("Waiting")).toHaveClass("chip-warning");
  });

  it("renders an optional prefix alongside the label", () => {
    render(<StatusChip prefix="Status:" label="under review" />);
    expect(screen.getByText("Status:")).toBeInTheDocument();
    expect(screen.getByText("under review")).toBeInTheDocument();
  });

  it("never applies green styling by default", () => {
    render(<StatusChip label="ready for review" />);
    expect(screen.getByText("ready for review")).not.toHaveClass(
      "chip-success",
    );
  });
});

describe("humanizeStatus", () => {
  it("replaces underscores with spaces for display", () => {
    expect(humanizeStatus("intake_started")).toBe("intake started");
    expect(humanizeStatus("under_review_support")).toBe(
      "under review support",
    );
  });
});
