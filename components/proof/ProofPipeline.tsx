import { proofResult } from "@/lib/proof/data";

// C. The actual pipeline: each stage of the validation harness with its
// application boundary and repository module, read from the artifact.
export default function ProofPipeline() {
  return (
    <section
      aria-labelledby="poc-pipeline-heading"
      className="border-t border-slate-100 bg-slate-50"
    >
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2
          id="poc-pipeline-heading"
          className="text-2xl font-bold tracking-tight text-slate-950"
        >
          The actual pipeline
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
          The validation harness talks to the same routes the browser uses. No
          test-only shortcut bypasses the production parser. Each stage names
          its application boundary and repository module.
        </p>
        <ol className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {proofResult.pipeline.map((stage, index) => (
            <li
              key={stage.stage}
              className="rounded-lg border border-slate-200 bg-white p-4"
            >
              <p className="text-xs font-semibold uppercase tracking-wider text-water-700">
                Stage {index + 1}
              </p>
              <p className="mt-1 text-sm font-semibold text-slate-900">
                {stage.stage}
              </p>
              <p className="mt-1 text-xs text-slate-500">{stage.boundary}</p>
              <p className="mt-1 break-all font-mono text-xs text-slate-500">
                {stage.module}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
