import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import SiteFooter from "@/components/SiteFooter";

afterEach(() => cleanup());

const LINKEDIN_URL = "https://www.linkedin.com/in/mpalmer1234/";
const GITHUB_URL = "https://github.com/mpalmer79/civil-engineer";

describe("SiteFooter professional badges", () => {
  it("renders a footer landmark", () => {
    render(<SiteFooter />);
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("links the LinkedIn badge to Michael Palmer's profile in a new tab", () => {
    render(<SiteFooter />);
    const link = screen.getByRole("link", {
      name: "Open Michael Palmer LinkedIn profile in a new tab",
    });
    expect(link).toHaveAttribute("href", LINKEDIN_URL);
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(link.textContent).toContain("LinkedIn");
    expect(link.textContent).toContain("Michael Palmer");
  });

  it("links the GitHub badge to the project repository in a new tab", () => {
    render(<SiteFooter />);
    const link = screen.getByRole("link", {
      name: "Open Civil Engineer AI GitHub repository in a new tab",
    });
    expect(link).toHaveAttribute("href", GITHUB_URL);
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(link.textContent).toContain("GitHub");
    expect(link.textContent).toContain("Project Repository");
  });

  it("keeps the existing footer navigation and disclaimer", () => {
    render(<SiteFooter />);
    expect(screen.getByText("Product")).toBeInTheDocument();
    expect(screen.getByText("Explore")).toBeInTheDocument();
    expect(
      screen.getByText(/brookside meadows is a fictional project/i),
    ).toBeInTheDocument();
  });

  it("contains no em dashes in footer copy", () => {
    const source = readFileSync(
      join(process.cwd(), "components/SiteFooter.tsx"),
      "utf8",
    );
    expect(source).not.toContain("\u2014");
  });
});
