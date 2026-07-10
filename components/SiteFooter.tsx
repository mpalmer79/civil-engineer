import Link from "next/link";

const productLinks = [
  { href: "/projects", label: "Projects" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/rule-packs", label: "Rule Packs" },
  { href: "/organizations", label: "Organizations" },
];

const exploreLinks = [
  { href: "/start-here", label: "Start Here" },
  { href: "/guided-demo", label: "Guided Demo" },
  { href: "/projects/proj_brookside_meadows", label: "Brookside Meadows" },
  { href: "/deployment-status", label: "Deployment Status" },
  {
    href: "https://civil-engineer.up.railway.app/",
    label: "Live demo",
    external: true,
  },
];

export default function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-[1.6fr_1fr_1fr]">
          <div className="max-w-md">
            <div className="flex items-center gap-2">
              <span
                aria-hidden="true"
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-water-600 to-land-600 text-sm font-bold text-white"
              >
                CE
              </span>
              <span className="text-sm font-semibold text-slate-900">
                Civil Engineer AI
              </span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              A document-first, evidence-first, reviewer-controlled stormwater
              review-support platform. It assists a human reviewer. It does not
              approve plans, certify compliance, validate design, or replace a
              licensed Professional Engineer.
            </p>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Product
            </p>
            <ul className="mt-3 space-y-2 text-sm">
              {productLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-slate-600 transition-colors hover:text-slate-900"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Explore
            </p>
            <ul className="mt-3 space-y-2 text-sm">
              {exploreLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-slate-600 transition-colors hover:text-slate-900"
                    {...(link.external
                      ? { target: "_blank", rel: "noreferrer" }
                      : {})}
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
          <a
            href="https://www.linkedin.com/in/mpalmer1234/"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open Michael Palmer LinkedIn profile in a new tab"
            className="flex items-center gap-3 rounded-lg bg-blue-700 px-4 py-2.5 text-white shadow-sm transition hover:bg-blue-800"
          >
            <svg
              viewBox="0 0 24 24"
              fill="currentColor"
              className="h-5 w-5 shrink-0"
              aria-hidden="true"
            >
              <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.36V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z" />
            </svg>

            <span className="text-left leading-tight">
              <span className="block text-[11px] font-medium text-blue-100">LinkedIn</span>
              <span className="block text-sm font-semibold">Michael Palmer</span>
            </span>
          </a>

          <a
            href="https://github.com/mpalmer79/civil-engineer"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open Civil Engineer AI GitHub repository in a new tab"
            className="flex items-center gap-3 rounded-lg bg-slate-900 px-4 py-2.5 text-white shadow-sm transition hover:bg-slate-800"
          >
            <svg
              viewBox="0 0 16 16"
              fill="currentColor"
              className="h-5 w-5 shrink-0"
              aria-hidden="true"
            >
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.28.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
            </svg>

            <span className="text-left leading-tight">
              <span className="block text-[11px] font-medium text-slate-300">GitHub</span>
              <span className="block text-sm font-semibold">Project Repository</span>
            </span>
          </a>
        </div>

        <p className="mt-8 border-t border-slate-100 pt-6 text-xs leading-relaxed text-slate-400">
          Brookside Meadows is a fictional project created for a portfolio
          software demonstration. All people, firms, documents, and values are
          synthetic. The build includes real project records, local
          authentication and access control, durable document storage, PDF page
          indexing, deterministic evidence retrieval, checklist review, an
          applicant response matrix, reviewer response packages, a reviewer
          dashboard, and deployment diagnostics. There are no live AI calls, no
          OCR, no enterprise single sign-on, and no full applicant portal yet.
        </p>
      </div>
    </footer>
  );
}
