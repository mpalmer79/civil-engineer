"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

export type NavLink = {
  href: string;
  label: string;
};

type MobileNavProps = {
  primaryLinks: NavLink[];
  demoModuleLinks: NavLink[];
};

export default function MobileNav({
  primaryLinks,
  demoModuleLinks,
}: MobileNavProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDetailsElement | null>(null);

  useEffect(() => {
    if (!menuOpen) return;

    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target;

      if (!(target instanceof Node)) return;

      if (!menuRef.current?.contains(target)) {
        setMenuOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [menuOpen]);

  const closeMenu = () => setMenuOpen(false);

  const toggleMenu = (event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    setMenuOpen((open) => !open);
  };

  return (
    <details ref={menuRef} className="group relative" open={menuOpen}>
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
