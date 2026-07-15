import { notProvenPoints, provenPoints } from "@/components/proof/content";

// H and I. What the validation proves and, stated just as plainly, what it
// does not prove. The determinations on the right belong to a licensed
// Professional Engineer and were not attempted.
export default function ProofProves() {
  return (
    <section
      aria-labelledby="poc-proves-heading"
      className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h2
            id="poc-proves-heading"
            className="text-xl font-bold tracking-tight text-slate-950"
          >
            What this proves
          </h2>
          <ul className="mt-4 space-y-2 text-sm text-slate-700">
            {provenPoints.map((point) => (
              <li key={point} className="flex gap-2">
                <span aria-hidden="true" className="text-water-700">
                  +
                </span>
                {point}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <h2 className="text-xl font-bold tracking-tight text-slate-950">
            What this does not prove
          </h2>
          <p className="mt-2 text-xs text-amber-800">
            These determinations belong to a licensed Professional Engineer
            and were not attempted:
          </p>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {notProvenPoints.map((point) => (
              <li key={point} className="flex gap-2">
                <span aria-hidden="true" className="text-amber-700">
                  -
                </span>
                {point}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
