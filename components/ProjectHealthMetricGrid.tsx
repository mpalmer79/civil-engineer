import Link from "next/link";
import type { ProjectHealthMetric } from "@/lib/api";

const severityStyles: Record<string, string> = {
  info: "border-slate-200 bg-white",
  low: "border-slate-200 bg-white",
  medium: "border-amber-200 bg-amber-50",
  high: "border-red-200 bg-red-50",
  needs_human_review: "border-amber-200 bg-amber-50",
};

// A grid of review-support health metrics aggregated from across the modules.
export default function ProjectHealthMetricGrid({
  metrics,
}: {
  metrics: ProjectHealthMetric[];
}) {
  if (metrics.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No health metrics yet.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Project health metrics
      </h3>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {metrics.map((metric) => (
          <Link
            key={metric.metricId}
            href={metric.sourceRoute}
            className={`rounded-lg border px-3 py-3 transition-colors hover:border-water-400 ${
              severityStyles[metric.severity] ?? severityStyles.info
            }`}
          >
            <div className="text-2xl font-bold text-slate-900">
              {metric.value}
            </div>
            <div className="mt-1 text-xs text-slate-600">{metric.label}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
