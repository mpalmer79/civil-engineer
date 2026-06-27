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
    <details className="relative" open={menuOpen}>
      <summary
        onClick={toggleMenu}
        className="flex cursor-pointer list-none items-center gap-1 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700"
      >
        Menu
        <span aria-hidden="true" className="text-[10px] text-slate-400">
          ▾
        </span>
      </summary>
      <div className="absolute right-0 z-50 mt-2 max-h-[70vh] w-64 overflow-y-auto rounded-lg border border-slate-200 bg-white p-2 shadow-lg">
        {primaryLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            onClick={closeMenu}
            className="block rounded-md px-2 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            {link.label}
          </Link>
        ))}
        <p className="mt-2 px-2 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          Demo modules
        </p>
        {demoModuleLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            onClick={closeMenu}
            className="block rounded-md px-2 py-1.5 text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900"
          >
            {link.label}
          </Link>
        ))}
      </div>
    </details>
  );
}
