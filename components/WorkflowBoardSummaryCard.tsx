import type { WorkflowBoardSummary } from "@/lib/api";

// Board-level counts for the reviewer workflow board. These are review-support
// counts, not a measure of approval, certification, or compliance.
function CountGrid({
  title,
  counts,
}: {
  title: string;
  counts: Record<string, number>;
}) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) {
    return null;
  }
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {entries.map(([key, value]) => (
          <span
            key={key}
            className="rounded-md bg-slate-50 px-2.5 py-1 text-xs text-slate-700"
          >
            {key.replace(/_/g, " ")}: <strong>{value}</strong>
          </span>
        ))}
      </div>
    </div>
  );
}

export default function WorkflowBoardSummaryCard({
  summary,
}: {
  summary: WorkflowBoardSummary | null;
}) {
  if (!summary) {
    return null;
  }
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">
          Workflow board summary
        </h3>
        <span className="text-sm text-slate-500">
          {summary.totalItems} items · {summary.openFollowUpCount} open
          follow-ups · {summary.readyForHandoffCount} ready for handoff
        </span>
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <CountGrid title="By status" counts={summary.itemsByStatus} />
        <CountGrid title="By severity" counts={summary.itemsBySeverity} />
        <CountGrid title="By section" counts={summary.itemsBySectionType} />
        <CountGrid title="By assigned role" counts={summary.itemsByAssignedRole} />
      </div>
      <p className="mt-4 text-xs text-slate-500">{summary.note}</p>
    </div>
  );
}
