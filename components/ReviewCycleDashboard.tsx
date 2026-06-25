import type { ReviewCycleDashboard as ReviewCycleDashboardData } from "@/lib/api";

function Stat({ value, label }: { value: number | string; label: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-3">
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="mt-1 text-xs text-slate-500">{label}</div>
    </div>
  );
}

// Summarizes the multi-round review cycle state for the project.
export default function ReviewCycleDashboard({
  dashboard,
}: {
  dashboard: ReviewCycleDashboardData | null;
}) {
  if (!dashboard) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        The review cycle dashboard is unavailable. Start the backend API to see
        review cycle counts.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Review cycle dashboard
      </h3>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <Stat value={dashboard.cycleCount} label="Review rounds" />
        <Stat value={dashboard.resubmittalCount} label="Resubmittals" />
        <Stat
          value={dashboard.applicantResponseCount}
          label="Applicant responses"
        />
        <Stat
          value={dashboard.unmappedResponseCount}
          label="Unmapped responses"
        />
        <Stat value={dashboard.comparisonRunCount} label="Revision comparisons" />
        <Stat value={dashboard.revisionChangeCount} label="Revision changes" />
        <Stat value={dashboard.carryForwardCount} label="Carried-forward items" />
        <Stat value={dashboard.openItemCount} label="Open resolution items" />
      </div>
      <p className="mt-4 text-xs text-slate-500">{dashboard.limitationsNote}</p>
    </div>
  );
}
