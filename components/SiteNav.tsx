"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import AccountNav from "@/components/AccountNav";
import MobileNav from "@/components/MobileNav";
import { getCurrentUser } from "@/lib/api";

// Global navigation with progressive disclosure. Visitors see the public
// product destinations only. Operational workspace destinations (projects,
// dashboard, queue, organizations) appear after sign-in, so the public
// experience is not dominated by authenticated modules. The older Brookside
// demo module routes remain reachable from the Technical Overview page and the
// Guided Demo rather than from the primary navigation.
const publicLinks = [
  { href: "/", label: "Product" },
  { href: "/guided-demo", label: "Guided Demo" },
  { href: "/start-here", label: "Technical Overview" },
  { href: "/pilot", label: "Pilot" },
];

const workspaceLinks = [
  { href: "/projects", label: "Projects" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/queue", label: "Reviewer Queue" },
  { href: "/workspace", label: "Workspace" },
  { href: "/organizations", label: "Organizations" },
  { href: "/rule-packs", label: "Rule Packs" },
];

export default function SiteNav() {
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    let active = true;
    getCurrentUser().then((user) => {
      if (active) setSignedIn(user !== null);
    });
    return () => {
      active = false;
    };
  }, []);

  const mobileLinks = signedIn
    ? [...publicLinks, ...workspaceLinks]
    : publicLinks;

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <nav
        aria-label="Primary"
        className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8"
      >
        <Link href="/" className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-water-600 to-land-600 text-sm font-bold text-white"
          >
            CE
          </span>
          <span className="flex flex-col leading-tight">
            <span className="text-sm font-semibold text-slate-900">
              Civil Engineer AI
            </span>
            <span className="text-[11px] text-slate-500">
              Stormwater Review Assistant
            </span>
          </span>
        </Link>

        {/* Desktop navigation */}
        <div className="hidden items-center gap-0.5 lg:flex">
          {publicLinks.map((link) => (
            <Link key={link.href} href={link.href} className="nav-link">
              {link.label}
            </Link>
          ))}

          {signedIn ? (
            <details className="group relative">
              <summary className="nav-link flex cursor-pointer list-none items-center gap-1">
                Workspace
                <span
                  aria-hidden="true"
                  className="text-[10px] text-slate-400 transition-transform group-open:rotate-180"
                >
                  ▾
                </span>
              </summary>
              <div className="menu-panel">
                <p className="menu-label">Reviewer workspace</p>
                {workspaceLinks.map((link) => (
                  <Link key={link.href} href={link.href} className="menu-item">
                    {link.label}
                  </Link>
                ))}
              </div>
            </details>
          ) : null}

          <span aria-hidden="true" className="mx-1 h-5 w-px bg-slate-200" />
          <AccountNav />
        </div>

        {/* Mobile navigation. The disclosure lives in a small client component
            so it collapses immediately after a client-side navigation while
            still exposing the full navigation on small screens. */}
        <div className="flex items-center gap-2 lg:hidden">
          <AccountNav />
          <MobileNav primaryLinks={mobileLinks} />
        </div>
      </nav>
    </header>
  );
}
