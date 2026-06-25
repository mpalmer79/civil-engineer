import type { ReviewCycle } from "@/lib/api";

const statusStyles: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600",
  active: "bg-water-50 text-water-700",
  reviewer_checked: "bg-water-50 text-water-700",
  ready_for_next_cycle: "bg-amber-50 text-amber-700",
  archived: "bg-slate-100 text-slate-500",
};

// Compact summary of a single review cycle.
export default function ReviewCycleSummaryCard({
  cycle,
}: {
  cycle: ReviewCycle | null;
}) {
  if (!cycle) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No active review cycle. Create one to begin a review round.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Review round {cycle.cycleNumber}
          </p>
          <h3 className="mt-1 text-lg font-semibold text-slate-900">
            {cycle.cycleName}
          </h3>
        </div>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
            statusStyles[cycle.status] ?? statusStyles.draft
          }`}
        >
          {cycle.status.replace(/_/g, " ")}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-600">{cycle.summary}</p>
    </div>
  );
}
