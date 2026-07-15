import { nextImprovements } from "@/components/proof/content";
import { proofResult } from "@/lib/proof/data";

// M. Known limitations, read from the artifact, alongside the actual roadmap.
export default function ProofNext() {
  return (
    <section
      aria-labelledby="poc-next-heading"
      className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"
    >
      <h2
        id="poc-next-heading"
        className="text-2xl font-bold tracking-tight text-slate-950"
      >
        Known limitations and next improvements
      </h2>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <h3 className="text-sm font-semibold text-slate-900">
            Current limitations, stated plainly
          </h3>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {proofResult.limitations.map((limitation) => (
              <li key={limitation} className="flex gap-2">
                <span aria-hidden="true" className="text-amber-700">
                  -
                </span>
                {limitation}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h3 className="text-sm font-semibold text-slate-900">
            The actual roadmap
          </h3>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {nextImprovements.map((item) => (
              <li key={item} className="flex gap-2">
                <span aria-hidden="true" className="text-water-700">
                  +
                </span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
