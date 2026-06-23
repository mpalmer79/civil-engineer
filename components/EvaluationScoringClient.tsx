"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  getAiReviewRuns,
  getRunEvaluation,
  runEvaluationScoring,
  type AiReviewRun,
  type EvaluationResult,
} from "@/lib/api";
import MetricCard from "@/components/MetricCard";

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export default function EvaluationScoringClient() {
  const [run, setRun] = useState<AiReviewRun | null>(null);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [backendUp, setBackendUp] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const runs = await getAiReviewRuns();
      setBackendUp(runs.length > 0 || true);
      if (runs.length > 0) {
        setRun(runs[0]);
        setResult(await getRunEvaluation(runs[0].reviewRunId));
      }
      setLoaded(true);
    })();
  }, []);

  const handleRun = useCallback(async () => {
    if (!run) return;
    setBusy(true);
    setMessage(null);
    const outcome = await runEvaluationScoring(run.reviewRunId);
    if (outcome.ok) {
      setResult(outcome.result);
    } else {
      setBackendUp(!outcome.backendDown);
      setMessage(outcome.message);
    }
    setBusy(false);
  }, [run]);

  if (!loaded) {
    return (
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
        Loading evaluation scoring.
      </p>
    );
  }

  if (!run) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-base font-semibold text-slate-900">
          Phase 5 evaluation scoring
        </h3>
        <p className="mt-2 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
          No AI review run was found. Start a run on the{" "}
          <Link
            href="/ai-review"
            className="font-semibold text-water-700 hover:text-water-600"
          >
            AI Review
          </Link>{" "}
          page, then return here to score it against the expected findings.
          Evaluation runs against backend data and is not faked in frontend-only
          mode.
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
              Scores the latest AI review run against the expected Brookside
              Meadows findings. This is a transparent, heuristic quality signal
              for human reviewers, not a certification of the AI or the package.
            </p>
            <p className="mt-2 text-xs font-mono text-slate-400">
              run: {run.reviewRunId}
            </p>
          </div>
          <button
            type="button"
            onClick={handleRun}
            disabled={busy}
            className="rounded-lg bg-land-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-land-700 disabled:opacity-60"
          >
            {busy ? "Scoring..." : "Run evaluation scoring"}
          </button>
        </div>
        {message ? (
          <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
            {message}
          </p>
        ) : null}
        {!result && !message ? (
          <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
            No evaluation result yet for this run. Click Run evaluation scoring to
            compute recall, precision, citation validity, and reviewer signals.
          </p>
        ) : null}
      </div>

      {result ? (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MetricCard value={pct(result.recall)} label="Recall" accent="water" />
            <MetricCard
              value={pct(result.precision)}
              label="Precision"
              accent="water"
            />
            <MetricCard
              value={`${result.matchedFindingsCount} / ${result.expectedFindingsCount}`}
              label="Matched expected findings"
              accent="land"
            />
            <MetricCard
              value={pct(result.overallScore)}
              label="Overall score"
              accent="land"
            />
          </div>

          <div className="surface-card p-6">
            <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Run signals
            </h4>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              <Signal label="Expected findings" value={result.expectedFindingsCount} />
              <Signal label="Draft findings" value={result.draftFindingsCount} />
              <Signal label="Matched findings" value={result.matchedFindingsCount} />
              <Signal
                label="Unmatched expected"
                value={result.unmatchedExpectedCount}
              />
              <Signal
                label="Extra draft findings"
                value={result.extraDraftFindingsCount}
              />
              <Signal
                label="Citation validity"
                value={pct(result.citationValidityRate)}
              />
              <Signal
                label="Human review required"
                value={pct(result.humanReviewRequiredRate)}
              />
              <Signal
                label="Prohibited words"
                value={result.prohibitedWordCount}
                bad={result.prohibitedWordCount > 0}
              />
              <Signal
                label="Validation failures"
                value={result.validationFailureCount}
              />
              <Signal label="Safety failures" value={result.safetyFailureCount} />
            </div>
          </div>

          <div className="surface-card overflow-hidden">
            <div className="border-b border-slate-200 px-4 py-3">
              <h4 className="text-sm font-semibold text-slate-700">
                Evaluation match table
              </h4>
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
                      <td className="px-4 py-3">
                        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                          {m.matchType.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-600">
                        {m.expectedFindingId ?? "-"}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-600">
                        {m.draftFindingId ?? "-"}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">
                        {m.matchedOn ?? "-"}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {m.matchConfidence > 0
                          ? `${Math.round(m.matchConfidence * 100)}%`
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

function Signal({
  label,
  value,
  bad = false,
}: {
  label: string;
  value: number | string;
  bad?: boolean;
}) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <div
        className={`text-lg font-bold ${bad ? "text-red-700" : "text-slate-900"}`}
      >
        {value}
      </div>
      <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </div>
    </div>
  );
}
