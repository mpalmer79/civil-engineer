import type { ResponsePackageAction } from "@/lib/api";

// A chronological list of reviewer actions recorded on a response package. This
// is review-support history, not a final engineering decision.
export default function ResponsePackageHistoryTimeline({
  actions,
}: {
  actions: ResponsePackageAction[];
}) {
  if (actions.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No reviewer actions recorded for this package yet.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Package history</h3>
      <ol className="mt-3 space-y-3">
        {actions.map((action) => (
          <li key={action.actionId} className="border-l-2 border-slate-200 pl-3">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="font-semibold text-slate-800">
                {action.actionType.replace(/_/g, " ")}
              </span>
              <span className="text-xs text-slate-500">
                {action.previousStatus.replace(/_/g, " ")} →{" "}
                {action.newStatus.replace(/_/g, " ")}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-600">{action.reviewerNote}</p>
            <p className="mt-0.5 text-xs text-slate-400">{action.reviewerName}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
