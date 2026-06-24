import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import WorkflowStatusBadge from "@/components/WorkflowStatusBadge";

describe("WorkflowStatusBadge", () => {
  it("renders a friendly label for a known status", () => {
    render(<WorkflowStatusBadge status="ready_for_handoff" />);
    expect(screen.getByText("ready for handoff")).toBeInTheDocument();
  });

  it("falls back to the raw status when unknown", () => {
    render(<WorkflowStatusBadge status="some_custom_status" />);
    expect(screen.getByText("some_custom_status")).toBeInTheDocument();
  });
});
