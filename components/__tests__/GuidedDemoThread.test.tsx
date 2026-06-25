import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import GuidedDemoThread, {
  guidedDemoFinding,
  guidedDemoSteps,
} from "@/components/GuidedDemoThread";

afterEach(cleanup);

describe("GuidedDemoThread", () => {
  it("renders the selected infiltration finding as the tracked concern", () => {
    render(<GuidedDemoThread />);
    expect(
      screen.getByText(guidedDemoFinding.title, { selector: "h2" }),
    ).toBeInTheDocument();
    expect(guidedDemoFinding.findingId).toBe("find_infiltration_missing");
  });

  it("walks the concern through every workflow stage", () => {
    render(<GuidedDemoThread />);
    const requiredModules = [
      "Checklist requirement",
      "Finding",
      "Source document and evidence reference",
      "Review packet item",
      "Workflow board item",
      "Draft response package language",
      "Human-review boundary",
    ];
    for (const moduleLabel of requiredModules) {
      expect(screen.getByText(moduleLabel)).toBeInTheDocument();
    }
    // The thread covers the full chain in order.
    expect(guidedDemoSteps.map((s) => s.module)).toEqual(requiredModules);
  });

  it("keeps every step inside the review-support boundary", () => {
    const text = guidedDemoSteps
      .flatMap((s) => [s.heading, s.body, ...(s.detail ?? [])])
      .join(" ")
      .toLowerCase();
    // The thread must not assert a final engineering determination.
    expect(text).not.toContain("approved");
    expect(text).not.toContain("certified");
    expect(text).not.toContain("compliant");
    expect(text).not.toMatch(/\bpassed\b/);
    // It must keep the human reviewer responsible.
    expect(text).toContain("human review");
  });
});
