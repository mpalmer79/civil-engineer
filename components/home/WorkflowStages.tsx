import Link from "next/link";

import { workflowStages } from "@/components/home/content";

// The six-stage reviewer workflow. Each stage links into the seeded Brookside
// Meadows workspace so a visitor can inspect the full module behind it.
export default function WorkflowStages() {
  return (
    <section
      aria-labelledby="workflow-heading"
      className="border-b border-slate-100 bg-slate-50"
    >
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2
          id="workflow-heading"
          className="text-xl font-semibold text-slate-950"
        >
          One reviewer journey, six stages
        </h2>

        <p className="mt-1 text-sm text-slate-600">
          Each stage links into the seeded Brookside Meadows workspace so you
          can inspect the full module behind it.
        </p>

        <ol className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workflowStages.map((stage) => (
            <li key={stage.stage}>
              <Link
                href={stage.href}
                className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-card transition hover:border-water-300 hover:shadow-card-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-water-600"
              >
                <span className="text-xs font-semibold uppercase tracking-wide text-water-700">
                  Stage {stage.stage}
                </span>

                <span className="mt-1 text-sm font-semibold text-slate-900">
                  {stage.title}
                </span>

                <span className="mt-2 text-xs leading-relaxed text-slate-600">
                  {stage.detail}
                </span>
              </Link>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
