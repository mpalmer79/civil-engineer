import Link from "next/link";

import StatusChip from "@/components/StatusChip";
import type { DemoJourneyStep } from "@/lib/demoJourney";

// Reusable demo step card for the Start Here demo path and the guided demo. It
// shows the step number, title, a short description, an optional "what to notice"
// note for evaluators, a category chip, and a link into the relevant Brookside
// Meadows route. Built on the shared visual system; it adds no new styling
// framework. Every linked step is review-support only.
export default function GuidedDemoCard({ step }: { step: DemoJourneyStep }) {
  return (
    <Link
      href={step.href}
      className="interactive-card flex h-full flex-col p-5"
      data-testid="demo-step-card"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-water-50 text-sm font-bold text-water-700">
          {step.step}
        </span>
        <StatusChip label={step.category} />
      </div>
      <h3 className="mt-3 text-base font-semibold text-slate-900">
        {step.title}
      </h3>
      <p className="mt-1 text-sm text-slate-600">{step.description}</p>
      {step.whatToNotice ? (
        <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
          <span className="font-semibold text-slate-700">What to notice: </span>
          {step.whatToNotice}
        </p>
      ) : null}
      <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-water-700">
        {step.label}
        <span aria-hidden="true">-&gt;</span>
      </span>
    </Link>
  );
}
