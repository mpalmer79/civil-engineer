import type { ReadyForHandoffSummary } from "@/lib/api";

// Lists the workflow items a reviewer has marked ready for handoff. Handoff
// means handing the organized review-support evidence to a licensed
// Professional Engineer. It is not an approval, certification, or final
// engineering decision.
export default function ReadyForHandoffPanel({
  summary,
}: {
  summary: ReadyForHandoffSummary | null;
}) {
  if (!summary) {
    return null;
  }
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">
          Ready for handoff
        </h3>
        <span className="text-sm text-slate-500">
          {summary.readyCount} of {summary.totalItems} items ·{" "}
          {summary.outstandingFollowUpCount} open follow-ups
        </span>
      </div>
      {summary.items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">
          No items are marked ready for handoff yet. Mark items ready for
          handoff from the board once a reviewer has worked them.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {summary.items.map((item) => (
            <li
              key={item.workflowItemId}
              className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            >
              <p className="font-medium text-slate-700">{item.title}</p>
              <p className="mt-0.5 text-xs text-slate-500">
                {item.sectionType.replace(/_/g, " ")} ·{" "}
                {item.assignedRole.replace(/_/g, " ")}
                {item.targetDate ? ` · target ${item.targetDate}` : ""}
              </p>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-4 text-xs text-slate-500">{summary.note}</p>
    </div>
  );
}
