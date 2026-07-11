import type { CadReviewFinding } from "@/lib/api";

const severityStyles: Record<string, string> = {
  high: "text-red-700",
  medium: "text-amber-700",
  low: "text-slate-600",
  info: "text-slate-600",
};

// Lists CAD review-support findings raised from the DXF metadata. Every finding
// is a draft that needs human review and does not approve, certify, verify, or
// validate anything.
export default function CadReviewFindingPanel({
  findings,
}: {
  findings: CadReviewFinding[];
}) {
  if (findings.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-600">
        No CAD review findings raised.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        CAD review findings
      </h3>
      <ul className="mt-3 space-y-3">
        {findings.map((finding) => (
          <li
            key={finding.cadReviewFindingId}
            className="rounded-md border border-slate-200 px-3 py-2"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-sm font-semibold text-slate-800">
                {finding.title}
              </span>
              <span className="flex items-center gap-2 text-xs">
                <span className={severityStyles[finding.severity] ?? "text-slate-600"}>
                  {finding.severity}
                </span>
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">
                  {finding.status.replace(/_/g, " ")}
                </span>
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-600">{finding.description}</p>
            <p className="mt-1 text-xs text-slate-500">
              {finding.findingType.replace(/_/g, " ")}
              {finding.linkedWorkflowItemId
                ? " · linked to workflow item"
                : ""}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
