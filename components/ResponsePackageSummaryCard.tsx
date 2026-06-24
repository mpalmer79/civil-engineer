import type { ResponsePackage, ResponsePackageSummary } from "@/lib/api";

const statusStyles: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600 ring-slate-300",
  needs_revision: "bg-amber-50 text-amber-700 ring-amber-600/20",
  reviewer_checked: "bg-land-50 text-land-700 ring-land-600/20",
  ready_for_handoff: "bg-water-50 text-water-700 ring-water-600/20",
  archived: "bg-slate-100 text-slate-500 ring-slate-300",
};

function CountRow({ counts }: { counts: Record<string, number> }) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([key, value]) => (
        <span
          key={key}
          className="rounded-md bg-slate-50 px-2.5 py-1 text-xs text-slate-700"
        >
          {key.replace(/_/g, " ")}: <strong>{value}</strong>
        </span>
      ))}
    </div>
  );
}

// Header card for a response package: title, audience, status, and item counts.
export default function ResponsePackageSummaryCard({
  pkg,
  summary,
}: {
  pkg: ResponsePackage;
  summary: ResponsePackageSummary | null;
}) {
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{pkg.title}</h3>
          <p className="mt-1 text-sm text-slate-500">
            Audience: {pkg.audienceType.replace(/_/g, " ")}
          </p>
        </div>
        <span
          className={`badge ${statusStyles[pkg.status] ?? statusStyles.draft}`}
        >
          {pkg.status.replace(/_/g, " ")}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-600">{pkg.summary}</p>
      {summary ? (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap gap-2 text-sm text-slate-600">
            <span>{summary.totalSections} sections</span>
            <span aria-hidden="true">·</span>
            <span>{summary.totalItems} items</span>
            <span aria-hidden="true">·</span>
            <span>{summary.totalAttachments} attachments</span>
            <span aria-hidden="true">·</span>
            <span>{summary.totalEvidenceLinks} evidence links</span>
          </div>
          <CountRow counts={summary.itemsByStatus} />
        </div>
      ) : null}
    </div>
  );
}
