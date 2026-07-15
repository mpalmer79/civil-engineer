import Link from "next/link";

// N. Onward navigation into the guided demo, the technical overview, the
// Brookside Meadows reference project, DXF intake, and the repository.
export default function ProofCta() {
  return (
    <section
      aria-labelledby="poc-cta-heading"
      className="border-t border-slate-100 bg-slate-50"
    >
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2
          id="poc-cta-heading"
          className="text-2xl font-bold tracking-tight text-slate-950"
        >
          Continue the technical review
        </h2>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/guided-demo"
            className="rounded-lg bg-water-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-water-800"
          >
            Start the guided demo
          </Link>
          <Link
            href="/start-here"
            className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white"
          >
            Review the technical overview
          </Link>
          <Link
            href="/projects/proj_brookside_meadows"
            className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white"
          >
            Explore Brookside Meadows
          </Link>
          <Link
            href="/projects/proj_brookside_meadows/cad"
            className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white"
          >
            Open DXF intake
          </Link>
          <a
            href="https://github.com/mpalmer79/civil-engineer"
            className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white"
          >
            Review the source-backed methodology
          </a>
        </div>
      </div>
    </section>
  );
}
