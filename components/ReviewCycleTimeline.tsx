import type { ReviewCycle } from "@/lib/api";

// A timeline of review rounds for the project.
export default function ReviewCycleTimeline({
  cycles,
  activeCycleId,
  onSelect,
}: {
  cycles: ReviewCycle[];
  activeCycleId: string | null;
  onSelect?: (reviewCycleId: string) => void;
}) {
  if (cycles.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No review rounds yet.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Review rounds</h3>
      <ol className="mt-4 space-y-3">
        {cycles.map((cycle) => {
          const selected = cycle.reviewCycleId === activeCycleId;
          return (
            <li key={cycle.reviewCycleId} className="flex gap-3">
              <div className="flex flex-col items-center">
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                    selected
                      ? "bg-water-600 text-white"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {cycle.cycleNumber}
                </span>
              </div>
              <button
                type="button"
                onClick={() => onSelect?.(cycle.reviewCycleId)}
                className={`flex-1 rounded-lg border px-3 py-2 text-left transition-colors ${
                  selected
                    ? "border-water-500 bg-water-50"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-slate-800">
                    {cycle.cycleName}
                  </span>
                  <span className="text-[11px] text-slate-500">
                    {cycle.status.replace(/_/g, " ")}
                  </span>
                </div>
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
