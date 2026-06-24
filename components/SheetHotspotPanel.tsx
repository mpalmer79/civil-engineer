"use client";

import type { PlanSheetHotspot } from "@/lib/api";

const SEVERITY_STYLE: Record<string, string> = {
  high: "bg-red-50 text-red-700 ring-red-600/20",
  medium: "bg-amber-50 text-amber-700 ring-amber-600/20",
  low: "bg-water-50 text-water-700 ring-water-600/20",
};

// Shows the details for the selected hotspot. The hotspot is seeded
// review-support metadata, never a verified plan location or a final decision.
export default function SheetHotspotPanel({
  hotspot,
  index,
}: {
  hotspot: PlanSheetHotspot | null;
  index: number | null;
}) {
  if (!hotspot) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-base font-semibold text-slate-900">
          Hotspot details
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          Select a numbered hotspot on the sheet preview to see its details and
          related review evidence.
        </p>
      </div>
    );
  }

  const severityStyle =
    SEVERITY_STYLE[hotspot.severity] ?? "bg-slate-100 text-slate-600 ring-slate-300";

  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center gap-2">
        {index != null ? (
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-water-600 text-xs font-bold text-white">
            {index + 1}
          </span>
        ) : null}
        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
          {hotspot.hotspotType.replace(/_/g, " ")}
        </span>
        <span className={`badge ${severityStyle}`}>
          {hotspot.severity} attention
        </span>
        {hotspot.requiresHumanReview ? (
          <span className="badge bg-amber-50 text-amber-700 ring-amber-600/20">
            needs human review
          </span>
        ) : null}
      </div>
      <h3 className="mt-3 text-base font-semibold text-slate-900">
        {hotspot.label}
      </h3>
      <p className="mt-2 text-sm text-slate-600">{hotspot.description}</p>
      {hotspot.reviewNote ? (
        <div className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          <span className="font-semibold text-slate-700">Review note: </span>
          {hotspot.reviewNote}
        </div>
      ) : null}
    </div>
  );
}
