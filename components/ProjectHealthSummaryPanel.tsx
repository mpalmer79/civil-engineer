import type { ProjectHealthSummary } from "@/lib/api";

// A compact project health summary card with the key review-support counts.
export default function ProjectHealthSummaryPanel({
  summary,
}: {
  summary: ProjectHealthSummary | null;
}) {
  if (!summary) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No health summary yet.
      </div>
    );
  }
  const rows = [
    { label: "Needs attention", value: summary.attentionCount },
    { label: "Ready for handoff", value: summary.readyForHandoffCount },
    { label: "Carried forward", value: summary.carryForwardCount },
    { label: "Needs more information", value: summary.needsMoreInformationCount },
    { label: "CAD findings", value: summary.cadFindingsCount },
    { label: "Resubmittals", value: summary.resubmittalCount },
    { label: "Open follow-ups", value: summary.openFollowUpCount },
    { label: "Response mapping gaps", value: summary.responseMappingGapCount },
    { label: "Revision changes to review", value: summary.revisionChangeCount },
    { label: "Readiness areas ready", value: summary.readinessReadyCount },
  ];
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Health summary</h3>
      <dl className="mt-4 space-y-1.5">
        {rows.map((row) => (
          <div
            key={row.label}
            className="flex items-center justify-between border-b border-slate-100 py-1 text-sm"
          >
            <dt className="text-slate-600">{row.label}</dt>
            <dd className="font-semibold text-slate-900">{row.value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-xs text-slate-500">{summary.limitationsNote}</p>
    </div>
  );
}
