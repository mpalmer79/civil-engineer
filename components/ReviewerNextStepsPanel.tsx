import Link from "next/link";
import type { ReviewerNextSteps } from "@/lib/api";

const severityStyles: Record<string, string> = {
  info: "bg-slate-100 text-slate-600",
  low: "bg-slate-100 text-slate-600",
  medium: "bg-amber-50 text-amber-700",
  high: "bg-red-50 text-red-700",
  needs_human_review: "bg-amber-50 text-amber-700",
};

// Recommended review-support next steps, highest severity first. None of these
// approves, certifies, or finalizes the work.
export default function ReviewerNextStepsPanel({
  nextSteps,
}: {
  nextSteps: ReviewerNextSteps | null;
}) {
  if (!nextSteps || nextSteps.steps.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No recommended next steps yet.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Recommended next steps
      </h3>
      <ol className="mt-4 space-y-2">
        {nextSteps.steps.map((step, index) => (
          <li
            key={`${step.title}-${index}`}
            className="rounded-lg border border-slate-200 px-3 py-2"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-sm font-medium text-slate-800">
                {index + 1}. {step.title}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] ${
                  severityStyles[step.severity] ?? severityStyles.info
                }`}
              >
                {step.severity.replace(/_/g, " ")}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-600">{step.detail}</p>
            <Link
              href={step.targetRoute}
              className="mt-1 inline-block text-xs font-semibold text-water-700 hover:text-water-600"
            >
              Go to {step.sourceModule.replace(/_/g, " ")}
            </Link>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-xs text-slate-500">{nextSteps.note}</p>
    </div>
  );
}
