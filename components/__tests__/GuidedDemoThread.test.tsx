import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import GuidedDemoThread from "@/components/GuidedDemoThread";

describe("GuidedDemoThread", () => {
  it("renders the selected infiltration finding end to end", () => {
    render(<GuidedDemoThread />);
    // The selected finding.
    expect(
      screen.getByText(
        /Infiltration testing not found for proposed infiltration basin/i,
      ),
    ).toBeInTheDocument();
    // The thread steps.
    for (const label of [
      "Checklist requirement",
      "Finding",
      "Source evidence",
      "Review packet item",
      "Workflow board item",
      "Draft response language",
      "Human-review boundary",
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    // Deep links into the modules.
    expect(
      screen.getByRole("link", { name: /Open the workflow board/i }),
    ).toHaveAttribute("href", "/workflow-board");
  });
});
