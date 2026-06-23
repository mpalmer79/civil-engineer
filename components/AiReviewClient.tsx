"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  getProviderMode,
  getAiReviewRuns,
  getRunDraftFindings,
  startAiReviewRun,
  getProjectChunks,
  getProjectReviewActions,
  runEvaluationScoring,
  getRunEvaluation,
  type ProviderModeInfo,
  type AiReviewRun,
  type AiDraftFinding,
  type ChunkItem,
  type HumanReviewAction,
  type EvaluationResult,
} from "@/lib/api";
import RiskBadge from "@/components/RiskBadge";

const riskFor = (level: string) =>
  level === "high" || level === "medium" || level === "low"
    ? (level as "high" | "medium" | "low")
    : "low";

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`badge ${
        ok
          ? "bg-land-50 text-land-700 ring-land-600/20"
          : "bg-red-50 text-red-700 ring-red-600/20"
      }`}
    >
      {label}
    </span>
  );
}

export default function AiReviewClient() {
  const [mode, setMode] = useState<ProviderModeInfo | null>(null);
  const [run, setRun] = useState<AiReviewRun | null>(null);
  const [drafts, setDrafts] = useState<AiDraftFinding[]>([]);
  const [chunks, setChunks] = useState<Record<string, ChunkItem>>({});
  const [actionsByDraft, setActionsByDraft] = useState<
    Record<string, HumanReviewAction>
  >({});
  const [loading, setLoading] = useState(false);
  const [backendUp, setBackendUp] = useState(true);
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalMessage, setEvalMessage] = useState<string | null>(null);

  const loadChunks = useCallback(async () => {
    const list = await getProjectChunks();
    const map: Record<string, ChunkItem> = {};
    for (const c of list) map[c.chunkId] = c;
    setChunks(map);
  }, []);

  const loadReviewActions = useCallback(async () => {
    const actions = await getProjectReviewActions();
    const latest: Record<string, HumanReviewAction> = {};
    // Actions arrive newest first; keep the first seen per draft.
    for (const a of actions) {
      if (!latest[a.draftFindingId]) latest[a.draftFindingId] = a;
    }
    setActionsByDraft(latest);
  }, []);

  useEffect(() => {
    (async () => {
      const m = await getProviderMode();
      setMode(m);
      setBackendUp(m !== null);
      await loadChunks();
      await loadReviewActions();
      const runs = await getAiReviewRuns();
      if (runs.length > 0) {
        setRun(runs[0]);
        setDrafts(await getRunDraftFindings(runs[0].reviewRunId));
        setEvaluation(await getRunEvaluation(runs[0].reviewRunId));
      }
    })();
  }, [loadChunks, loadReviewActions]);

  const handleStart = useCallback(async () => {
    setLoading(true);
    setEvaluation(null);
    setEvalMessage(null);
    const newRun = await startAiReviewRun();
    if (newRun) {
      setBackendUp(true);
      setRun(newRun);
      setDrafts(await getRunDraftFindings(newRun.reviewRunId));
      await loadReviewActions();
    } else {
      setBackendUp(false);
    }
    setLoading(false);
  }, [loadReviewActions]);

  const handleEvaluate = useCallback(async () => {
    if (!run) return;
    setEvaluating(true);
    setEvalMessage(null);
    const outcome = await runEvaluationScoring(run.reviewRunId);
    if (outcome.ok) {
      setEvaluation(outcome.result);
    } else {
      setEvalMessage(outcome.message);
    }
    setEvaluating(false);
  }, [run]);

  const validDrafts = drafts.filter(
    (d) => d.validationStatus === "validation_passed",
  );
  const failedDrafts = drafts.filter(
    (d) => d.validationStatus === "validation_failed",
  );

  return (
    <div className="space-y-8">
      {/* Provider mode and run control */}
      <div className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              AI Review Assistant
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              {mode
                ? mode.detail
                : "Provider mode loads from the backend. Start the API to run an AI review."}
            </p>
            {mode ? (
              <div className="mt-2 flex flex-wrap gap-2">
                <span className="badge bg-water-50 text-water-700 ring-water-600/20">
                  provider: {mode.provider}
                </span>
                <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                  mode: {mode.mode}
                </span>
                <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                  model: {mode.modelName}
                </span>
                <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                  live calls: {mode.liveCallsEnabled ? "enabled" : "disabled"}
                </span>
              </div>
            ) : null}
          </div>
          <button
            type="button"
            onClick={handleStart}
            disabled={loading}
            className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {loading ? "Running AI review..." : "Start AI review"}
          </button>
        </div>
        {!backendUp ? (
          <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
            The backend is not reachable. Start the API to run a controlled AI
            review with the mock provider.
          </p>
        ) : null}
      </div>

      {/* Run summary */}
      {run ? (
        <div className="surface-card p-6">
          <h3 className="text-base font-semibold text-slate-900">
            Review run summary
          </h3>
          <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Summary label="Run" value={run.reviewRunId} mono />
            <Summary label="Status" value={run.status} />
            <Summary
              label="Checklist items"
              value={String(run.checklistItemCount)}
            />
            <Summary
              label="Draft findings"
              value={String(run.draftFindingsCreated)}
            />
            <Summary label="Provider" value={run.provider} />
            <Summary label="Model" value={run.modelName} />
            <Summary label="Prompt" value={run.promptVersion} mono />
            <Summary
              label="Validation failures"
              value={String(run.safetyFailures)}
            />
          </div>
          <p className="mt-4 text-xs italic text-slate-400">
            Draft findings are review-support output for human evaluation, not
            final engineering conclusions. Every draft requires human review.
          </p>
        </div>
      ) : null}

      {/* Next steps: human review and evaluation scoring */}
      {run ? (
        <div className="surface-card p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                Next steps
              </h3>
              <p className="mt-1 text-sm text-slate-600">
                Route these draft findings to a human reviewer, then score the
                run against the expected Brookside Meadows findings.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/human-review"
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                Go to Human Review Queue
              </Link>
              <button
                type="button"
                onClick={handleEvaluate}
                disabled={evaluating}
                className="rounded-lg bg-land-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-land-700 disabled:opacity-60"
              >
                {evaluating ? "Scoring..." : "Run evaluation scoring"}
              </button>
            </div>
          </div>
          {evalMessage ? (
            <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
              {evalMessage}
            </p>
          ) : null}
          {evaluation ? (
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Summary
                label="Recall"
                value={`${Math.round(evaluation.recall * 100)}%`}
              />
              <Summary
                label="Precision"
                value={`${Math.round(evaluation.precision * 100)}%`}
              />
              <Summary
                label="Matched"
                value={`${evaluation.matchedFindingsCount} / ${evaluation.expectedFindingsCount}`}
              />
              <Summary
                label="Overall score"
                value={`${Math.round(evaluation.overallScore * 100)}%`}
              />
              <p className="col-span-2 text-xs text-slate-500 sm:col-span-4">
                Full metrics and the match table are on the{" "}
                <Link
                  href="/evaluation"
                  className="font-semibold text-water-700 hover:text-water-600"
                >
                  Evaluation
                </Link>{" "}
                page.
              </p>
            </div>
          ) : null}
        </div>
      ) : null}

      {/* Draft findings */}
      {validDrafts.length > 0 ? (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-900">
            Draft review-support findings ({validDrafts.length})
          </h3>
          <div className="grid gap-4 lg:grid-cols-2">
            {validDrafts.map((d) => (
              <article key={d.draftFindingId} className="surface-card p-6">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                    Draft finding
                  </span>
                  <span className="badge bg-water-50 text-water-700 ring-water-600/20">
                    {d.findingType.replace(/_/g, " ")}
                  </span>
                  <RiskBadge level={riskFor(d.riskLevel)} />
                </div>
                <h4 className="mt-3 text-base font-semibold text-slate-900">
                  {d.title}
                </h4>
                <p className="mt-2 text-sm text-slate-600">{d.summary}</p>
                <div className="mt-3 text-sm">
                  <p className="font-semibold text-slate-700">
                    Recommended human action
                  </p>
                  <p className="mt-0.5 text-slate-600">
                    {d.recommendedHumanAction}
                  </p>
                </div>

                <div className="mt-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Evidence used
                  </p>
                  <ul className="mt-1 space-y-1">
                    {d.sourceChunkIds.map((cid) => (
                      <li
                        key={cid}
                        className="rounded-md bg-slate-50 px-2 py-1 text-xs text-slate-600"
                      >
                        <span className="font-mono">{cid}</span>
                        {chunks[cid] ? (
                          <>
                            {" "}
                            <span className="text-slate-400">
                              ({chunks[cid].fileName}
                              {chunks[cid].pageNumber != null
                                ? `, page ${chunks[cid].pageNumber}`
                                : ""}
                              )
                            </span>
                            <span className="block text-slate-600">
                              {chunks[cid].content}
                            </span>
                          </>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3 text-xs">
                  <StatusPill
                    ok={d.validationStatus === "validation_passed"}
                    label={`validation: ${d.validationStatus}`}
                  />
                  <StatusPill
                    ok={d.safetyCheckStatus === "safety_check_passed"}
                    label={`safety: ${d.safetyCheckStatus}`}
                  />
                  {actionsByDraft[d.draftFindingId] ? (
                    <span className="badge bg-land-50 text-land-700 ring-land-600/20">
                      human review:{" "}
                      {actionsByDraft[d.draftFindingId].action.replace(
                        /_/g,
                        " ",
                      )}
                    </span>
                  ) : (
                    <span className="badge bg-yellow-50 text-yellow-700 ring-yellow-600/20">
                      {d.status === "requires_human_review"
                        ? "Human review pending"
                        : d.status.replace(/_/g, " ")}
                    </span>
                  )}
                  <span className="font-mono text-slate-400">
                    confidence {Math.round(d.confidence * 100)}%
                  </span>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : run ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
          No valid draft findings in this run.
        </p>
      ) : null}

      {/* Validation failures */}
      {failedDrafts.length > 0 ? (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-900">
            Validation failures ({failedDrafts.length})
          </h3>
          <p className="text-sm text-slate-600">
            These draft outputs failed validation or safety checks. They are
            shown as failures only and are not usable review findings until they
            are reviewed or regenerated.
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            {failedDrafts.map((d) => (
              <article
                key={d.draftFindingId}
                className="surface-card border-l-4 border-red-300 p-6"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge bg-red-50 text-red-700 ring-red-600/20">
                    Validation failure
                  </span>
                  <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                    {d.checklistItemId}
                  </span>
                  <span className="font-mono text-xs text-slate-400">
                    {d.draftFindingId}
                  </span>
                </div>
                <h4 className="mt-3 text-base font-semibold text-slate-900">
                  {d.title}
                </h4>
                <p className="mt-2 text-sm font-medium text-red-700">
                  This failed draft is not a usable review finding until it is
                  reviewed or regenerated.
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                  <StatusPill
                    ok={false}
                    label={`validation: ${d.validationStatus}`}
                  />
                  <StatusPill
                    ok={d.safetyCheckStatus === "safety_check_passed"}
                    label={`safety: ${d.safetyCheckStatus}`}
                  />
                  <span className="font-mono text-slate-400">
                    evidence: {d.sourceChunkIds.join(", ") || "none"}
                  </span>
                </div>
                {d.validationErrors.length > 0 ? (
                  <ul className="mt-3 space-y-1">
                    {d.validationErrors.map((err, i) => (
                      <li
                        key={i}
                        className="rounded-md bg-red-50 px-2 py-1 text-xs text-red-700"
                      >
                        {err}
                      </li>
                    ))}
                  </ul>
                ) : null}
                <p className="mt-3 text-xs text-slate-500">
                  Manage failed drafts on the{" "}
                  <Link
                    href="/human-review"
                    className="font-semibold text-water-700 hover:text-water-600"
                  >
                    Human Review Queue
                  </Link>
                  . A failed draft cannot be accepted.
                </p>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Summary({
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
