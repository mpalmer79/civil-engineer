import type { RevisionComparisonRun } from "@/lib/api";

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-center">
      <div className="text-xl font-bold text-slate-900">{value}</div>
      <div className="text-[11px] text-slate-500">{label}</div>
    </div>
  );
}

// Summary card for a single revision comparison run.
export default function RevisionComparisonSummaryCard({
  run,
}: {
  run: RevisionComparisonRun | null;
}) {
  if (!run) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Run a revision comparison to see the summary.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">
          Revision comparison
        </h3>
        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-600">
          {run.status.replace(/_/g, " ")}
        </span>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat value={run.addedCount} label="Added" />
        <Stat value={run.removedCount} label="Removed" />
        <Stat value={run.changedCount} label="Changed" />
        <Stat value={run.unchangedCount} label="Unchanged" />
      </div>
      <p className="mt-3 text-sm text-slate-600">{run.summary}</p>
      <p className="mt-2 text-xs text-slate-500">{run.limitationsNote}</p>
    </div>
  );
}
