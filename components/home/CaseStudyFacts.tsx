import DemoDataBadge from "@/components/DemoDataBadge";
import { caseStudyFacts } from "@/components/home/content";

// Fixed facts about the Brookside Meadows reference project, counted from the
// seeded fixture. Brookside Meadows is a synthetic reference project used for
// product evaluation, and the section labels it as such.
export default function CaseStudyFacts() {
  return (
    <section
      aria-labelledby="case-study-heading"
      className="border-b border-slate-100"
    >
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-end">
          <div>
            <h2
              id="case-study-heading"
              className="text-xl font-semibold text-slate-950"
            >
              The Brookside Meadows reference project
            </h2>

            <p className="mt-1 text-sm text-slate-600">
              Fixed facts from the seeded review fixture, not live operational
              metrics.
            </p>
          </div>

          <DemoDataBadge />
        </div>

        <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {caseStudyFacts.map((fact) => (
            <div
              key={fact.label}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-card"
            >
              <dd className="text-2xl font-bold text-slate-950">
                {fact.value}
              </dd>

              <dt className="mt-1 text-xs text-slate-500">{fact.label}</dt>
            </div>
          ))}
        </dl>

        <p className="mt-4 text-xs text-slate-500">
          The ten planted issues, including a design storm discrepancy, missing
          infiltration testing, a basin naming conflict, and a missing revised
          sheet, are documented in the project story and traced through every
          module. The same concern remains inspectable from intake through
          reviewer handoff.
        </p>
      </div>
    </section>
  );
}
