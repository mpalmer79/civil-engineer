import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import SiteFooter from "@/components/SiteFooter";

afterEach(() => cleanup());

describe("PageHeader", () => {
  it("renders the eyebrow, title, description, and actions", () => {
    render(
      <PageHeader
        eyebrow="Account"
        title="Sign in"
        description="Access your review records."
        actions={<button type="button">Do thing</button>}
      />,
    );
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByText("Account")).toBeInTheDocument();
    expect(screen.getByText("Access your review records.")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Do thing" }),
    ).toBeInTheDocument();
  });

  it("renders without optional props", () => {
    const { container } = render(<PageHeader title="Just a title" />);
    expect(
      screen.getByRole("heading", { name: "Just a title" }),
    ).toBeInTheDocument();
    // The title uses the shared design-system class.
    expect(container.querySelector(".page-title")).not.toBeNull();
  });
});

describe("EmptyState", () => {
  it("renders a readable title, description, and optional action", () => {
    const { container } = render(
      <EmptyState
        title="No accessible projects yet"
        description="Create a project or open the demo."
        action={<a href="/projects/new">Create a project record</a>}
      />,
    );
    expect(screen.getByText("No accessible projects yet")).toBeInTheDocument();
    expect(
      screen.getByText("Create a project or open the demo."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Create a project record" }),
    ).toBeInTheDocument();
    expect(container.querySelector(".empty-state")).not.toBeNull();
  });
});

describe("SiteFooter", () => {
  it("renders the product name and a review-support boundary line", () => {
    render(<SiteFooter />);
    expect(screen.getByText("Civil Engineer AI")).toBeInTheDocument();
    const boundary = screen.getByText(/does not\s+approve plans/i);
    expect(boundary).toBeInTheDocument();
  });

  it("links to product, demo, and deployment status surfaces", () => {
    render(<SiteFooter />);
    expect(screen.getByRole("link", { name: "Projects" })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Guided Demo" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Deployment Status" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Live demo" })).toBeInTheDocument();
    // Start Here and the Brookside Meadows sample project are discoverable from
    // the footer for demo navigation.
    expect(
      screen.getByRole("link", { name: "Start Here" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Brookside Meadows" }),
    ).toBeInTheDocument();
  });

  it("does not contain attribution or prohibited final-decision wording", () => {
    const { container } = render(<SiteFooter />);
    const text = (container.textContent ?? "").toLowerCase();
    for (const bad of [
      ["claude", "code"].join(" "),
      ["claude.ai", "code"].join("/"),
      ["generated", "by"].join(" "),
      ["co-authored", "by"].join("-"),
    ]) {
      expect(text).not.toContain(bad);
    }
    // Affirmative final-decision claims must not appear (negated boundary
    // wording such as "does not approve" is allowed).
    for (const phrase of [
      "plan approved",
      "design validated",
      "fully compliant",
      "passed review",
    ]) {
      expect(text).not.toContain(phrase);
    }
  });
});
