import type { CadIntakeDashboard as CadIntakeDashboardData } from "@/lib/api";

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-3">
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="mt-1 text-xs text-slate-500">{label}</div>
    </div>
  );
}

function CountRow({ counts }: { counts: Record<string, number> }) {
  const entries = Object.entries(counts);
  if (entries.length === 0) {
    return <p className="text-xs text-slate-400">None</p>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([key, count]) => (
        <span
          key={key}
          className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
        >
          {key.replace(/_/g, " ")}: {count}
        </span>
      ))}
    </div>
  );
}

// Summarizes CAD intake for the project: file counts, parse queue and validation
// status breakdowns, and how many CAD findings remain unpromoted. These counts
// organize review-support work; they do not approve, certify, or validate
// anything.
export default function CadIntakeDashboard({
  dashboard,
}: {
  dashboard: CadIntakeDashboardData | null;
}) {
  if (!dashboard) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        The CAD intake dashboard is unavailable. Start the backend API to see
        intake counts.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        CAD intake dashboard
      </h3>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <Stat value={dashboard.totalFiles} label="Uploaded CAD files" />
        <Stat value={dashboard.filesNeedingParse} label="Files needing parse" />
        <Stat
          value={dashboard.filesWithParseFailures}
          label="Parse failures (technical)"
        />
        <Stat
          value={dashboard.parseRunsNeedingHumanReview}
          label="Parse runs needing human review"
        />
        <Stat value={dashboard.totalFindings} label="CAD findings" />
        <Stat
          value={dashboard.unpromotedFindingsCount}
          label="Unpromoted findings"
        />
        <Stat
          value={dashboard.promotedFindingsCount}
          label="Promoted to workflow"
        />
      </div>

      <div className="mt-5 space-y-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Parse queue status
          </p>
          <div className="mt-1">
            <CountRow counts={dashboard.queueStatusCounts} />
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Upload validation status
          </p>
          <div className="mt-1">
            <CountRow counts={dashboard.validationStatusCounts} />
          </div>
        </div>
      </div>

      <p className="mt-4 text-xs text-slate-500">{dashboard.limitationsNote}</p>
    </div>
  );
}
