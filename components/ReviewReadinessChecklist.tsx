import type { ReviewReadinessCheck } from "@/lib/api";

const statusStyles: Record<string, string> = {
  not_started: "bg-slate-100 text-slate-500",
  needs_attention: "bg-amber-50 text-amber-700",
  in_review: "bg-water-50 text-water-700",
  ready_for_human_review: "bg-water-50 text-water-700",
  reviewer_checked: "bg-water-50 text-water-700",
};

// The review readiness checklist. ready for human review means an area is
// organized enough for human review, never that it is complete or approved.
export default function ReviewReadinessChecklist({
  checks,
}: {
  checks: ReviewReadinessCheck[];
}) {
  if (checks.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No readiness checks yet.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Review readiness checklist
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        Human review signoff is always required. The dashboard never marks the
        project complete, approved, or certified.
      </p>
      <ul className="mt-4 space-y-2">
        {checks.map((check) => (
          <li
            key={check.readinessCheckId}
            className="rounded-lg border border-slate-200 px-3 py-2"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-sm font-medium text-slate-800">
                {check.label}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] ${
                  statusStyles[check.status] ?? statusStyles.in_review
                }`}
              >
                {check.status.replace(/_/g, " ")}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-600">{check.description}</p>
            {check.blockerCount > 0 ? (
              <p className="mt-1 text-xs text-amber-700">
                {check.blockerCount} item(s) need attention. {check.recommendedNextStep}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
