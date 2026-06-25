import type { ProjectCommandCenterSnapshot } from "@/lib/api";

const statusStyles: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600",
  active_review: "bg-water-50 text-water-700",
  needs_attention: "bg-red-50 text-red-700",
  ready_for_handoff: "bg-amber-50 text-amber-700",
  needs_more_information: "bg-amber-50 text-amber-700",
  reviewer_checked: "bg-water-50 text-water-700",
};

// Top-level command center summary for the project: overall status and the
// review-support summary. Not a final decision.
export default function CommandCenterSummaryCard({
  snapshot,
}: {
  snapshot: ProjectCommandCenterSnapshot | null;
}) {
  if (!snapshot) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No command center snapshot yet. Generate one to see the project state.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Project review state
          </p>
          <h3 className="mt-1 text-lg font-semibold text-slate-900">
            Brookside Meadows command center
          </h3>
        </div>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
            statusStyles[snapshot.overallStatus] ?? statusStyles.active_review
          }`}
        >
          {snapshot.overallStatus.replace(/_/g, " ")}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-600">{snapshot.summary}</p>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Needs attention", value: snapshot.attentionCount },
          { label: "Ready for handoff", value: snapshot.readyForHandoffCount },
          { label: "Carried forward", value: snapshot.carryForwardCount },
          { label: "Mapping gaps", value: snapshot.responseMappingGapCount },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-center"
          >
            <div className="text-xl font-bold text-slate-900">{stat.value}</div>
            <div className="text-[11px] text-slate-500">{stat.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
