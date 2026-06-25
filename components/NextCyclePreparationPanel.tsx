"use client";

import type { NextCyclePreparation } from "@/lib/api";

// Shows the next-cycle preparation summary and lets a reviewer regenerate it.
// This summary organizes review-support work for the next round. It is not a
// final decision and does not approve, certify, or close anything.
export default function NextCyclePreparationPanel({
  preparation,
  busy,
  onPrepare,
}: {
  preparation: NextCyclePreparation | null;
  busy: boolean;
  onPrepare: () => void;
}) {
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">
          Next-cycle preparation
        </h3>
        <button
          type="button"
          onClick={onPrepare}
          disabled={busy}
          className="rounded-lg bg-water-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Working..." : "Prepare next cycle"}
        </button>
      </div>
      {preparation ? (
        <div className="mt-4">
          <div className="grid grid-cols-3 gap-3">
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
              <div className="text-[11px] text-slate-500">
                Needs more information
              </div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-center">
              <div className="text-xl font-bold text-slate-900">
                {preparation.reviewerCheckedCount}
              </div>
              <div className="text-[11px] text-slate-500">Reviewer checked</div>
            </div>
          </div>
          <p className="mt-3 text-sm text-slate-600">{preparation.summary}</p>
          <p className="mt-2 text-xs text-slate-500">
            Status: {preparation.status.replace(/_/g, " ")}. Next response package
            {preparation.nextResponsePackageReady
              ? " can be prepared"
              : " not yet ready"}
            .
          </p>
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">
          No next-cycle preparation yet. Generate one to see what should move into
          the next review round.
        </p>
      )}
    </div>
  );
}
