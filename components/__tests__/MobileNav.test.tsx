import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

// next/link renders a plain anchor in jsdom, so the mobile menu can be exercised
// without a router. The close behavior is driven by React state, not by a real
// navigation.
import MobileNav, { type NavLink } from "@/components/MobileNav";

const primaryLinks: NavLink[] = [
  { href: "/", label: "Home" },
  { href: "/projects", label: "Projects" },
  { href: "/guided-demo", label: "Guided Demo" },
];

function renderMobileNav() {
  return render(<MobileNav primaryLinks={primaryLinks} />);
}

function getMenu() {
  return screen.getByText("Menu").closest("details") as HTMLDetailsElement;
}

afterEach(() => cleanup());

describe("MobileNav", () => {
  it("renders the mobile menu trigger", () => {
    renderMobileNav();
    expect(screen.getByText("Menu")).toBeTruthy();
  });

  it("starts collapsed and opens when the menu trigger is clicked", () => {
    renderMobileNav();
    const menu = getMenu();
    expect(menu.open).toBe(false);

    fireEvent.click(screen.getByText("Menu"));
    expect(menu.open).toBe(true);

    // The primary links are exposed once the menu is open.
    expect(screen.getByText("Projects")).toBeTruthy();
    expect(screen.getByText("Guided Demo")).toBeTruthy();
  });

  it("closes the menu after a top-level nav link is clicked", () => {
    renderMobileNav();
    const menu = getMenu();

    fireEvent.click(screen.getByText("Menu"));
    expect(menu.open).toBe(true);

    fireEvent.click(screen.getByText("Projects"));
    expect(menu.open).toBe(false);
  });

  it("keeps the Guided Demo discoverable", () => {
    renderMobileNav();
    fireEvent.click(screen.getByText("Menu"));
    expect(screen.getByText("Guided Demo")).toBeTruthy();
  });

  it("does not surface tool attribution or final-decision wording", () => {
    renderMobileNav();
    fireEvent.click(screen.getByText("Menu"));
    const text = document.body.textContent ?? "";
    for (const forbidden of [
      ["Generated", "by"].join(" "),
      ["Claude", "Code"].join(" "),
      "approved",
      "certified",
      "compliant",
    ]) {
      expect(text).not.toContain(forbidden);
    }
  });
});
