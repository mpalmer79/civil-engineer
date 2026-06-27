import Link from "next/link";

const productLinks = [
  { href: "/projects", label: "Projects" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/rule-packs", label: "Rule Packs" },
  { href: "/organizations", label: "Organizations" },
];

const exploreLinks = [
  { href: "/guided-demo", label: "Guided Demo" },
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

        <p className="mt-10 border-t border-slate-100 pt-6 text-xs leading-relaxed text-slate-400">
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
