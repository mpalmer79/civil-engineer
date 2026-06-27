import Link from "next/link";

import AccountNav from "@/components/AccountNav";

// Primary product navigation, ordered so the current review-support workflows
// are visible first. The Sprint 9 reviewer dashboard and reviewer queue lead the
// operational workflow alongside Projects. The Account/Login control renders
// separately through AccountNav.
const primaryLinks = [
  { href: "/", label: "Home" },
  { href: "/projects", label: "Projects" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/queue", label: "Reviewer Queue" },
  { href: "/rule-packs", label: "Rule Packs" },
  { href: "/organizations", label: "Organizations" },
  { href: "/guided-demo", label: "Guided Demo" },
];

// Older Brookside Meadows demo modules. These remain fully available; they are
// grouped here so they do not dominate the primary navigation. They stay easy to
// reach from the Demo modules menu and from the Guided Demo.
const demoModuleLinks = [
  { href: "/project-dashboard", label: "Project Dashboard" },
  { href: "/project", label: "Project" },
  { href: "/documents", label: "Documents" },
  { href: "/checklist", label: "Checklist" },
  { href: "/findings", label: "Findings" },
  { href: "/plan-sheets", label: "Plan Sheets" },
  { href: "/cad-intake", label: "CAD Intake" },
  { href: "/cad-review", label: "CAD Review" },
  { href: "/sheet-viewer", label: "Sheet Viewer" },
  { href: "/review-packet", label: "Review Packet" },
  { href: "/workflow-board", label: "Workflow Board" },
  { href: "/response-package", label: "Response Package" },
  { href: "/review-cycles", label: "Review Cycles" },
  { href: "/ai-review", label: "AI Review" },
  { href: "/human-review", label: "Human Review" },
  { href: "/audit", label: "Audit" },
  { href: "/evaluation", label: "Evaluation" },
  { href: "/deployment-status", label: "Deployment Status" },
];

export default function SiteNav() {
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
        <div className="hidden items-center gap-1 md:flex">
          {primaryLinks.map((link) => (
            <Link key={link.href} href={link.href} className="nav-link">
              {link.label}
            </Link>
          ))}

          {/* Demo modules disclosure. Native details/summary keeps the grouped
              demo routes discoverable and accessible without client JavaScript. */}
          <details className="group relative">
            <summary className="nav-link flex cursor-pointer list-none items-center gap-1">
              Demo modules
              <span aria-hidden="true" className="text-[10px] text-slate-400">
                ▾
              </span>
            </summary>
            <div className="absolute right-0 z-50 mt-2 grid w-64 grid-cols-1 gap-0.5 rounded-lg border border-slate-200 bg-white p-2 shadow-lg">
              <p className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                Brookside Meadows demo
              </p>
              {demoModuleLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="rounded-md px-2 py-1.5 text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </details>

          <AccountNav />
        </div>

        {/* Mobile navigation. A native details disclosure exposes the full
            navigation on small screens instead of hiding it behind the account
            control only. */}
        <div className="flex items-center gap-2 md:hidden">
          <details className="relative">
            <summary className="flex cursor-pointer list-none items-center gap-1 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700">
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
                  className="block rounded-md px-2 py-1.5 text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </details>
          <AccountNav />
        </div>
      </nav>
    </header>
  );
}
