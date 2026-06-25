import type { RevisionChangeRecord } from "@/lib/api";

const changeStyles: Record<string, string> = {
  added: "bg-water-50 text-water-700",
  removed: "bg-red-50 text-red-700",
  changed: "bg-amber-50 text-amber-700",
  carried_forward: "bg-amber-50 text-amber-700",
  unchanged: "bg-slate-100 text-slate-500",
};

// A table of review-support revision change records between two DXF parse rounds.
// These describe extracted metadata differences only, not engineering judgments.
export default function RevisionChangeTable({
  changes,
  hideUnchanged,
}: {
  changes: RevisionChangeRecord[];
  hideUnchanged?: boolean;
}) {
  const rows = hideUnchanged
    ? changes.filter((c) => c.changeType !== "unchanged")
    : changes;
  if (rows.length === 0) {
    return (
      <p className="text-sm text-slate-500">No revision changes to show.</p>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-3 py-2">Change</th>
            <th className="px-3 py-2">Category</th>
            <th className="px-3 py-2">Previous</th>
            <th className="px-3 py-2">Current</th>
            <th className="px-3 py-2">Severity</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((change) => (
            <tr
              key={change.changeRecordId}
              className="border-b border-slate-100"
            >
              <td className="px-3 py-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] ${
                    changeStyles[change.changeType] ?? changeStyles.unchanged
                  }`}
                >
                  {change.changeType.replace(/_/g, " ")}
                </span>
              </td>
              <td className="px-3 py-2 text-slate-600">
                {change.sourceCategory.replace(/_/g, " ")}
              </td>
              <td className="px-3 py-2 text-slate-600">
                {change.previousValue ?? "-"}
              </td>
              <td className="px-3 py-2 text-slate-600">
                {change.currentValue ?? "-"}
              </td>
              <td className="px-3 py-2 text-slate-500">{change.severity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
