import type { NextCyclePreparation } from "@/lib/api";

// Read-only next-cycle preparation summary for the review cycle detail page.
export default function NextCyclePreparationReadOnly({
  preparation,
}: {
  preparation: NextCyclePreparation | null;
}) {
  if (!preparation) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No next-cycle preparation has been generated for this review cycle yet.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Next-cycle preparation
      </h3>
      <div className="mt-4 grid grid-cols-3 gap-3">
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-center">
          <div className="text-xl font-bold text-slate-900">
            {preparation.carriedForwardCount}
          </div>
          <div className="text-[11px] text-slate-500">Carried forward</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-center">
          <div className="text-xl font-bold text-slate-900">
            {preparation.needsMoreInformationCount}
          </div>
          <div className="text-[11px] text-slate-500">Needs more information</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-center">
          <div className="text-xl font-bold text-slate-900">
            {preparation.reviewerCheckedCount}
          </div>
          <div className="text-[11px] text-slate-500">Reviewer checked</div>
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-600">{preparation.summary}</p>
    </div>
  );
}
