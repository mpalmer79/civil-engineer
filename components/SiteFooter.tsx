import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="max-w-md">
            <p className="text-sm font-semibold text-slate-900">
              Civil Engineer AI: Stormwater Review Assistant
            </p>
            <p className="mt-2 text-sm text-slate-600">
              A review-support and evidence-organization prototype for land
              development workflows. It assists a human reviewer, it does not
              approve plans, certify compliance, or replace a licensed
              Professional Engineer.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-x-10 gap-y-2 text-sm">
            <Link
              href="/projects"
              className="text-slate-600 hover:text-slate-900"
            >
              Projects
            </Link>
            <Link
              href="/rule-packs"
              className="text-slate-600 hover:text-slate-900"
            >
              Rule Packs
            </Link>
            <Link
              href="/organizations"
              className="text-slate-600 hover:text-slate-900"
            >
              Organizations
            </Link>
            <Link
              href="/guided-demo"
              className="text-slate-600 hover:text-slate-900"
            >
              Guided Demo
            </Link>
          </div>
        </div>
        <p className="mt-8 text-xs text-slate-400">
          Brookside Meadows is a fictional project created for a portfolio
          software demonstration. All people, firms, documents, and values are
          synthetic. The build includes real project records, local
          authentication and access control, durable document storage, PDF page
          indexing, deterministic evidence retrieval, checklist review, an
          applicant response matrix, and reviewer response packages. There are no
          live AI calls, no OCR, no enterprise single sign-on, and no full
          applicant portal yet.
        </p>
      </div>
    </footer>
  );
}
