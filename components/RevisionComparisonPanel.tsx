"use client";

import { useState } from "react";
import type { CadParseRun, RevisionChangeRecord, RevisionComparisonRun } from "@/lib/api";
import RevisionComparisonSummaryCard from "@/components/RevisionComparisonSummaryCard";
import RevisionChangeTable from "@/components/RevisionChangeTable";

// Lets a reviewer pick a previous and current DXF parse run and run a
// review-support revision comparison, then shows the change records. Comparison
// uses extracted DXF metadata only and does not verify CAD or validate design.
export default function RevisionComparisonPanel({
  parseRuns,
  run,
  changes,
  busy,
  onRun,
}: {
  parseRuns: CadParseRun[];
  run: RevisionComparisonRun | null;
  changes: RevisionChangeRecord[];
  busy: boolean;
  onRun: (previousParseRunId: string, currentParseRunId: string) => void;
}) {
  const completed = parseRuns.filter((r) =>
    ["completed", "completed_with_warnings"].includes(r.status),
  );
  const [previousId, setPreviousId] = useState("");
  const [currentId, setCurrentId] = useState("");
  const [hideUnchanged, setHideUnchanged] = useState(true);

  return (
    <div className="space-y-4">
      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Compare DXF parse rounds
        </h3>
        <p className="mt-1 text-sm text-slate-600">
          Select a previous and a current parsed DXF file to compare extracted
          metadata between rounds. This compares layers, references, blocks, and
          review findings only. It does not verify CAD or validate design.
        </p>
        {completed.length < 2 ? (
          <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
            At least two completed DXF parse runs are needed to compare rounds.
            Parse a resubmittal DXF in CAD Intake first.
          </p>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Previous round
              </label>
              <select
                value={previousId}
                onChange={(e) => setPreviousId(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-2 py-2 text-sm"
              >
                <option value="">Select parse run...</option>
                {completed.map((r) => (
                  <option key={r.parseRunId} value={r.parseRunId}>
                    {r.parseRunId} ({r.entityCount} entities)
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Current round
              </label>
              <select
                value={currentId}
                onChange={(e) => setCurrentId(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-2 py-2 text-sm"
              >
                <option value="">Select parse run...</option>
                {completed.map((r) => (
                  <option key={r.parseRunId} value={r.parseRunId}>
                    {r.parseRunId} ({r.entityCount} entities)
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              onClick={() => onRun(previousId, currentId)}
              disabled={
                busy || !previousId || !currentId || previousId === currentId
              }
              className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-water-700 disabled:opacity-60"
            >
              {busy ? "Comparing..." : "Run comparison"}
            </button>
          </div>
        )}
      </div>

      <RevisionComparisonSummaryCard run={run} />

      {run ? (
        <div className="surface-card p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-lg font-semibold text-slate-900">
              Revision changes
            </h3>
            <label className="flex items-center gap-2 text-xs text-slate-600">
              <input
                type="checkbox"
                checked={hideUnchanged}
                onChange={(e) => setHideUnchanged(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300"
              />
              Hide unchanged
            </label>
          </div>
          <div className="mt-4">
            <RevisionChangeTable changes={changes} hideUnchanged={hideUnchanged} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
