import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import SitePlanIllustration from "@/components/illustrations/SitePlanIllustration";
import WorkflowStepIcon, {
  type WorkflowStepKey,
} from "@/components/illustrations/WorkflowStepIcon";
import MetricIcon, {
  type MetricIconKey,
} from "@/components/illustrations/MetricIcon";
import ArchitectureDiagram from "@/components/illustrations/ArchitectureDiagram";
import BoundaryMark from "@/components/illustrations/BoundaryMark";

// Status or engineering-decision words that must never appear as embedded text
// in a decorative illustration. The illustrations carry no text at all, so this
// guards against a regression that introduces a label.
const FORBIDDEN_TERMS = [
  "approved",
  "certified",
  "compliant",
  "noncompliant",
  "verified",
  "passed",
  "failed",
  "safe",
  "unsafe",
  "design validated",
  "pe stamp",
  "professional engineer",
];

const workflowKeys: WorkflowStepKey[] = [
  "intake",
  "metadata",
  "findings",
  "packet",
  "workflow",
  "response",
  "resubmittal",
  "command-center",
];

const metricKeys: MetricIconKey[] = [
  "site-acres",
  "proposed-lots",
  "disturbed-acres",
  "documents",
  "checklist",
  "review-issues",
  "evaluation",
];

function assertDecorativeSvg(svg: SVGSVGElement | null) {
  expect(svg).not.toBeNull();
  // Decorative: hidden from assistive technology.
  expect(svg!.getAttribute("aria-hidden")).toBe("true");
  // No embedded text inside the illustration.
  expect(svg!.querySelectorAll("text").length).toBe(0);
  expect(svg!.querySelectorAll("tspan").length).toBe(0);
  // No forbidden status wording anywhere in the markup.
  const markup = svg!.outerHTML.toLowerCase();
  for (const term of FORBIDDEN_TERMS) {
    expect(markup).not.toContain(term);
  }
}

describe("homepage illustrations", () => {
  it("hero site-plan illustration is decorative and text-free", () => {
    const { container } = render(<SitePlanIllustration />);
    assertDecorativeSvg(container.querySelector("svg"));
  });

  it("architecture diagram is decorative and text-free", () => {
    const { container } = render(<ArchitectureDiagram />);
    assertDecorativeSvg(container.querySelector("svg"));
  });

  it("boundary mark is decorative and text-free", () => {
    const { container } = render(<BoundaryMark />);
    assertDecorativeSvg(container.querySelector("svg"));
  });

  it("renders a decorative icon for every workflow step", () => {
    for (const step of workflowKeys) {
      const { container } = render(<WorkflowStepIcon step={step} />);
      assertDecorativeSvg(container.querySelector("svg"));
    }
  });

  it("renders a decorative watermark for every metric", () => {
    for (const icon of metricKeys) {
      const { container } = render(<MetricIcon icon={icon} />);
      assertDecorativeSvg(container.querySelector("svg"));
    }
  });
});
