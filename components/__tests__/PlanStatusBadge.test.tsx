import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PlanStatusBadge from "@/components/PlanStatusBadge";

describe("PlanStatusBadge", () => {
  it("renders a friendly label for a known status", () => {
    render(<PlanStatusBadge status="needs_follow_up" />);
    expect(screen.getByText("needs follow up")).toBeInTheDocument();
  });

  it("falls back to the raw status when unknown", () => {
    render(<PlanStatusBadge status="some_custom_status" />);
    expect(screen.getByText("some_custom_status")).toBeInTheDocument();
  });
});
