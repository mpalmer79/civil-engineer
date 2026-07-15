import { proofResult } from "@/lib/proof/data";

// G. Review-support findings: deterministic-rule findings from the artifact,
// each carrying its evidence and requiring human review.
export default function ProofFindings() {
  return (
    <section
      aria-labelledby="poc-findings-heading"
      className="border-t border-slate-100 bg-slate-50"
    >
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2
          id="poc-findings-heading"
          className="text-2xl font-bold tracking-tight text-slate-950"
        >
          Review-support findings
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
          Every finding below came from a deterministic rule, carries its
          evidence, and requires human review. None of them is a violation
          determination: that judgment belongs to a licensed reviewer through
          an authorized workflow. Note what is absent: DETENTION BASIN 1 and
          INFILTRATION BASIN 1 share the number 1 but are different facility
          types, so the parser no longer pairs them as a conflict.
        </p>
        <ul className="mt-6 grid gap-4 lg:grid-cols-2">
          {proofResult.findings.map((finding) => (
            <li
              key={finding.title}
              className="rounded-lg border border-slate-200 bg-white p-5"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                  {finding.finding_type.replace(/_/g, " ")}
                </span>
                <span className="inline-flex rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">
                  attention: {finding.severity}
                </span>
                <span className="inline-flex rounded-full bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-600">
                  deterministic rule
                </span>
              </div>
              <h3 className="mt-3 text-sm font-semibold text-slate-900">
                {finding.title}
              </h3>
              <p className="mt-1 text-xs leading-relaxed text-slate-600">
                {finding.description}
              </p>
              <p className="mt-2 text-xs font-medium text-water-700">
                Reviewer action: confirm or dismiss with project context.
              </p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
