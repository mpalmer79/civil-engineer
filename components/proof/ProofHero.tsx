import { proofResult } from "@/lib/proof/data";

// A. Hero: the technical validation headline, the synthetic disclosure, the
// snapshot identifier, and the download entry points. The download anchors
// hit route handlers that stream files, so next/link does not apply.
export default function ProofHero() {
  return (
    <section
      aria-labelledby="poc-hero-heading"
      className="border-b border-slate-100 bg-gradient-to-b from-slate-50 to-white"
    >
      <div className="mx-auto max-w-6xl px-4 pb-12 pt-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-semibold uppercase tracking-wider text-water-700">
            Technical validation report
          </p>
          <h1
            id="poc-hero-heading"
            className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl"
          >
            Proof of Concept: DXF Intake and Review Support
          </h1>
          <p className="mt-4 text-base leading-relaxed text-slate-600">
            A synthetic, structurally valid civil-site DXF was processed
            through the real Civil Engineer AI upload and parse services. The
            results below demonstrate deterministic DXF metadata extraction,
            consistency checking, reference identification, and
            reviewer-support analysis. They do not demonstrate engineering
            approval or design correctness.
          </p>
          <p className="mt-3 text-sm text-slate-500">
            The drawing is synthetic. It is not a real survey, not a real
            submission, and not suitable for construction. Snapshot{" "}
            <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-700">
              {proofResult.snapshot_id}
            </code>
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <a
              href="#poc-results-heading"
              className="rounded-lg bg-water-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-water-800"
            >
              Explore the results
            </a>
            {/* These anchors hit a route handler that streams a file
                download, not a page, so next/link does not apply. */}
            {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
            <a
              href="/api/proof-of-concept/download/proof-bundle"
              className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Download the test bundle
            </a>
            {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
            <a
              href="/api/proof-of-concept/download/proof-report"
              className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              View the integration report
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
