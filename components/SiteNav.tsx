import Link from "next/link";

const links = [
  { href: "/", label: "Home" },
  { href: "/guided-demo", label: "Guided Demo" },
  { href: "/project-dashboard", label: "Project Dashboard" },
  { href: "/project", label: "Project" },
  { href: "/documents", label: "Documents" },
  { href: "/checklist", label: "Checklist" },
  { href: "/findings", label: "Findings" },
  { href: "/plan-sheets", label: "Plan Sheets" },
  { href: "/cad-review", label: "CAD Review" },
  { href: "/sheet-viewer", label: "Sheet Viewer" },
  { href: "/review-packet", label: "Review Packet" },
  { href: "/workflow-board", label: "Workflow Board" },
  { href: "/response-package", label: "Response Package" },
  { href: "/review-cycles", label: "Review Cycles" },
  { href: "/cad-intake", label: "CAD Intake" },
  { href: "/ai-review", label: "AI Review" },
  { href: "/human-review", label: "Human Review" },
  { href: "/audit", label: "Audit" },
  { href: "/evaluation", label: "Evaluation" },
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
        <div className="hidden items-center gap-1 md:flex">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className="nav-link">
              {link.label}
            </Link>
          ))}
        </div>
        <div className="md:hidden">
          <span className="badge bg-slate-100 text-slate-600 ring-slate-200">
            Review Support
          </span>
        </div>
      </nav>
    </header>
  );
}
