import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import MetricCard from "@/components/MetricCard";

describe("MetricCard", () => {
  it("renders the value and label without an icon", () => {
    const { container } = render(<MetricCard value={42} label="Site acres" />);
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("Site acres")).toBeInTheDocument();
    // No decorative watermark when no icon is provided.
    expect(container.querySelector("svg")).toBeNull();
  });

  it("renders an optional hint", () => {
    render(<MetricCard value="38.5" label="Site acres" hint="seeded fixture" />);
    expect(screen.getByText("seeded fixture")).toBeInTheDocument();
  });

  it("renders a faint corner watermark when an icon is provided", () => {
    const { container } = render(
      <MetricCard
        value={47}
        label="Proposed lots"
        icon={<svg data-testid="metric-icon" aria-hidden="true" />}
      />,
    );
    // Value and label still render correctly alongside the watermark.
    expect(screen.getByText("47")).toBeInTheDocument();
    expect(screen.getByText("Proposed lots")).toBeInTheDocument();
    const icon = container.querySelector('[data-testid="metric-icon"]');
    expect(icon).not.toBeNull();
    // The watermark is decorative and hidden from assistive technology.
    const wrapper = icon!.parentElement;
    expect(wrapper?.getAttribute("aria-hidden")).toBe("true");
  });
});
