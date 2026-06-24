"use client";

import { useState } from "react";
import {
  compareCadReferencesToPlanSheets,
  type CadPlanSheetComparison,
} from "@/lib/api";

// Runs and shows the comparison of extracted sheet and detail references against
// the seeded plan sheets. Matching is review support, not verification.
export default function CadPlanSheetComparisonPanel({
  parseRunId,
  onComparisonRun,
}: {
  parseRunId: string;
  onComparisonRun?: () => void;
}) {
  const [comparison, setComparison] = useState<CadPlanSheetComparison | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleCompare = async () => {
    setBusy(true);
    setMessage(null);
    const result = await compareCadReferencesToPlanSheets(parseRunId);
    if (result) {
      setComparison(result);
      onComparisonRun?.();
    } else {
      setMessage(
        "The backend is not reachable. Start the API to compare references to plan sheets.",
      );
    }
    setBusy(false);
  };

  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">
          Plan sheet comparison
        </h3>
        <button
          type="button"
          onClick={handleCompare}
          disabled={busy}
          className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Comparing..." : "Compare to plan sheets"}
        </button>
      </div>

      {message ? (
        <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
          {message}
        </p>
      ) : null}

      {comparison ? (
        <div className="mt-4">
          <p className="text-sm text-slate-600">
            {comparison.matchedCount} matched · {comparison.unmatchedCount}{" "}
            unmatched of {comparison.totalCandidates} sheet and detail references
          </p>
          <ul className="mt-3 space-y-2">
            {comparison.rows.map((row) => (
              <li
                key={row.candidateId}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm"
              >
                <span className="font-medium text-slate-800">
                  {row.referenceText}
                </span>
                <span className="text-xs text-slate-500">
                  {row.matchedSheetNumber
                    ? `matched ${row.matchedSheetNumber}`
                    : "no plan sheet match"}{" "}
                  · {row.confidenceLabel.replace(/_/g, " ")}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-slate-500">{comparison.note}</p>
        </div>
      ) : null}
    </div>
  );
}
