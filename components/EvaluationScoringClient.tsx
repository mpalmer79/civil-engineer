"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getAiReviewRuns,
  getRunEvaluation,
  runEvaluation,
  type AiReviewRun,
  type AiEvaluationResult,
} from "@/lib/api";
import MetricCard from "@/components/MetricCard";

function pct(n: number): string {
  return `${Math.round(n * 100)}%`;
}

const MATCH_LABELS: Record<string, string> = {
  related_checklist_match: "Related checklist match",
  exact_category_match: "Category match",
  title_similarity_match: "Title similarity",
  unmatched_expected: "Unmatched expected finding",
  extra_draft: "Extra draft finding",
};

export default function EvaluationScoringClient() {
  const [run, setRun] = useState<AiReviewRun | null>(null);
  const [result, setResult] = useState<AiEvaluationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [backendUp, setBackendUp] = useState(true);

  useEffect(() => {
    (async () => {
      const runs = await getAiReviewRuns();
      if (runs.length === 0) {
        setBackendUp(false);
        return;
      }
      setBackendUp(true);
      setRun(runs[0]);
      setResult(await getRunEvaluation(runs[0].reviewRunId));
    })();
  }, []);

  const handleRun = useCallback(async () => {
    if (!run) return;
    setBusy(true);
    setMessage(null);
    const res = await runEvaluation(run.reviewRunId);
    if (res.ok && res.result) {
      setResult(res.result);
      setMessage("Evaluation scoring completed for the latest review run.");
    } else {
      setMessage(res.error ?? "Evaluation scoring failed.");
      if (!res.backendReachable) setBackendUp(false);
    }
    setBusy(false);
  }, [run]);

  if (!backendUp || !run) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-base font-semibold text-slate-900">
          Phase 5 evaluation scoring
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          Evaluation scoring runs against a completed AI review run. Start a run
          on the{" "}
          <a
            href="/ai-review"
            className="font-semibold text-water-700 hover:text-water-600"
          >
            AI Review
          </a>{" "}
          page, then return here to score it against the expected findings.
        </p>
        <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
          The backend is required for live evaluation scoring. Evaluation
          results are persisted by the API and are not simulated in the browser.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Phase 5 evaluation scoring
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              Score the latest AI review run against the expected Brookside
              Meadows findings. Matching is heuristic and explainable, not a
              final engineering determination.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="badge bg-water-50 text-water-700 ring-water-600/20">
                run: {run.reviewRunId}
              </span>
              <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                provider: {run.provider}
              </span>
              <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                drafts created: {run.draftFindingsCreated}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRun}
            disabled={busy}
            className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Scoring..." : "Run evaluation scoring"}
          </button>
        </div>
        {message ? (
          <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
            {message}
          </p>
        ) : null}
      </div>

      {result ? (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MetricCard
              value={pct(result.recall)}
              label="Recall"
              hint={`${result.matchedFindingsCount} / ${result.expectedFindingsCount} expected matched`}
              accent="land"
            />
            <MetricCard
              value={pct(result.precision)}
              label="Precision"
              hint={`${result.matchedFindingsCount} / ${result.draftFindingsCount} valid drafts matched`}
              accent="water"
            />
            <MetricCard
              value={pct(result.citationValidityRate)}
              label="Citation validity rate"
              accent="water"
            />
            <MetricCard
              value={pct(result.overallScore)}
              label="Overall score"
              hint="Heuristic, weighted"
              accent="land"
            />
          </div>

          <div className="surface-card p-6">
            <h4 className="text-base font-semibold text-slate-900">
              Run scoring summary
            </h4>
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3 lg:grid-cols-4">
              <Stat label="Last review run" value={result.reviewRunId} mono />
              <Stat
                label="Expected findings"
                value={String(result.expectedFindingsCount)}
              />
              <Stat
                label="Draft findings (valid)"
                value={String(result.draftFindingsCount)}
              />
              <Stat
                label="Matched findings"
                value={String(result.matchedFindingsCount)}
              />
              <Stat
                label="Unmatched expected"
                value={String(result.unmatchedExpectedCount)}
              />
              <Stat
                label="Extra draft findings"
                value={String(result.extraDraftFindingsCount)}
              />
              <Stat
                label="Human review required rate"
                value={pct(result.humanReviewRequiredRate)}
              />
              <Stat
                label="Prohibited word count"
                value={String(result.prohibitedWordCount)}
              />
              <Stat
                label="Validation failures"
                value={String(result.validationFailureCount)}
              />
              <Stat
                label="Safety failures"
                value={String(result.safetyFailureCount)}
              />
            </div>
          </div>

          <div className="surface-card overflow-hidden">
            <div className="border-b border-slate-100 px-4 py-3">
              <h4 className="text-base font-semibold text-slate-900">
                Evaluation match table
              </h4>
              <p className="mt-1 text-xs text-slate-500">
                Each row shows how a draft finding was matched to an expected
                finding, or that an item was unmatched or extra.
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Match type</th>
                    <th className="px-4 py-3">Expected finding</th>
                    <th className="px-4 py-3">Draft finding</th>
                    <th className="px-4 py-3">Matched on</th>
                    <th className="px-4 py-3">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {result.matches.map((m) => (
                    <tr key={m.evaluationMatchId} className="hover:bg-slate-50">
                      <td className="px-4 py-3 text-slate-700">
                        {MATCH_LABELS[m.matchType] ?? m.matchType}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">
                        {m.expectedFindingId ?? "-"}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">
                        {m.draftFindingId ?? "-"}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {m.matchedOn ?? "-"}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {m.matchConfidence > 0
                          ? m.matchConfidence.toFixed(2)
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <p className="text-xs italic text-slate-400">
            Evaluation scoring is a transparent, heuristic review-support
            measure. It does not certify the AI output or make a final
            engineering determination.
          </p>
        </>
      ) : (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
          No evaluation result for this run yet. Use Run evaluation scoring to
          score it against the expected findings.
        </p>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div
        className={`mt-1 text-sm font-semibold text-slate-900 ${
          mono ? "font-mono break-all" : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}
