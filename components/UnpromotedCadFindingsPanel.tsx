import type { UnpromotedCadFinding } from "@/lib/api";

const severityStyles: Record<string, string> = {
  high: "bg-red-50 text-red-700",
  medium: "bg-amber-50 text-amber-700",
  low: "bg-slate-100 text-slate-600",
};

// Lists CAD review findings that have not yet been promoted to a workflow item,
// with checkboxes for batch promotion and a per-finding promote action. Every
// finding is a review-support draft that needs human review. Promotion does not
// approve, certify, or validate anything.
export default function UnpromotedCadFindingsPanel({
  findings,
  selectedIds,
  onToggle,
  onToggleAll,
  onPromoteOne,
  busyId,
}: {
  findings: UnpromotedCadFinding[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  onToggleAll: () => void;
  onPromoteOne: (id: string) => void;
  busyId: string | null;
}) {
  if (findings.length === 0) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Unpromoted CAD findings
        </h3>
        <p className="mt-2 text-sm text-slate-500">
          No unpromoted CAD findings. Every CAD review finding has been promoted
          to the workflow board or excluded.
        </p>
      </div>
    );
  }
  const allSelected = findings.every((f) =>
    selectedIds.has(f.cadReviewFindingId),
  );
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">
          Unpromoted CAD findings
        </h3>
        <button
          type="button"
          onClick={onToggleAll}
          className="text-xs font-semibold text-water-700 hover:text-water-600"
        >
          {allSelected ? "Clear selection" : "Select all"}
        </button>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        Select findings to promote into the workflow board. Each remains a
        review-support draft under human review.
      </p>
      <ul className="mt-4 space-y-2">
        {findings.map((finding) => (
          <li
            key={finding.cadReviewFindingId}
            className="rounded-lg border border-slate-200 px-3 py-3"
          >
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={selectedIds.has(finding.cadReviewFindingId)}
                onChange={() => onToggle(finding.cadReviewFindingId)}
                className="mt-1 h-4 w-4 rounded border-slate-300"
                aria-label={`Select finding ${finding.title}`}
              />
              <div className="flex-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-medium text-slate-800">
                    {finding.title}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] ${
                      severityStyles[finding.severity] ?? severityStyles.low
                    }`}
                  >
                    {finding.severity}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {finding.findingType.replace(/_/g, " ")}
                </p>
                <p className="mt-1 text-sm text-slate-600">
                  {finding.description}
                </p>
                <button
                  type="button"
                  onClick={() => onPromoteOne(finding.cadReviewFindingId)}
                  disabled={busyId === finding.cadReviewFindingId}
                  className="mt-2 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
                >
                  {busyId === finding.cadReviewFindingId
                    ? "Promoting..."
                    : "Promote to workflow"}
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
