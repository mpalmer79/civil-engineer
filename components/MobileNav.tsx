"use client";

import { useState } from "react";
import Link from "next/link";

export type NavLink = {
  href: string;
  label: string;
};

type MobileNavProps = {
  primaryLinks: NavLink[];
  demoModuleLinks: NavLink[];
};

// Client wrapper for the small-screen navigation. The native details/summary
// disclosure stays accessible, but its open state is controlled by React so the
// menu collapses immediately after a client-side navigation. Without this, the
// disclosure would remain open after a link is selected and keep covering the
// page content.
export default function MobileNav({
  primaryLinks,
  demoModuleLinks,
}: MobileNavProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  // Close the mobile menu after any navigation link is selected, including the
  // grouped Demo modules links.
  const closeMenu = () => setMenuOpen(false);

  // Controlled toggling for the disclosure. preventDefault keeps the native open
  // state in sync with React state instead of letting the browser flip it
  // independently. The summary still responds to mouse and keyboard, so the menu
  // remains accessible.
  const toggleMenu = (event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    setMenuOpen((open) => !open);
  };

  return (
    <details className="group relative" open={menuOpen}>
      <summary
        onClick={toggleMenu}
        className="btn btn-secondary btn-sm cursor-pointer list-none"
      >
        <span className="sr-only">Toggle navigation menu</span>
        Menu
        <span
          aria-hidden="true"
          className="text-[10px] text-slate-400 transition-transform group-open:rotate-180"
        >
          ▾
        </span>
      </summary>
      <div className="menu-panel max-h-[70vh] overflow-y-auto">
        <p className="menu-label">Navigate</p>
        {primaryLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            onClick={closeMenu}
            className="menu-item font-medium text-slate-700"
          >
            {link.label}
          </Link>
        ))}
        <p className="menu-label mt-2 border-t border-slate-100 pt-3">
          Demo modules
        </p>
        {demoModuleLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            onClick={closeMenu}
            className="menu-item"
          >
            {link.label}
          </Link>
        ))}
      </div>
    </details>
  );
}
