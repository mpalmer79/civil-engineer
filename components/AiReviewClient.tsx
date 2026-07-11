"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getProviderMode,
  getAiReviewRuns,
  getRunDraftFindings,
  startAiReviewRun,
  getProjectChunks,
  getProjectReviewActions,
  type ProviderModeInfo,
  type AiReviewRun,
  type AiDraftFinding,
  type ChunkItem,
  type HumanReviewAction,
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
  const [reviewActions, setReviewActions] = useState<
    Record<string, HumanReviewAction[]>
  >({});
  const [loading, setLoading] = useState(false);
  const [backendUp, setBackendUp] = useState(true);

  const loadChunks = useCallback(async () => {
    const listResult = await getProjectChunks();
    const map: Record<string, ChunkItem> = {};
    if (listResult.ok) {
      for (const c of listResult.data) map[c.chunkId] = c;
    }
    setChunks(map);
  }, []);

  const loadReviewActions = useCallback(async () => {
    const actsResult = await getProjectReviewActions();
    const grouped: Record<string, HumanReviewAction[]> = {};
    if (actsResult.ok) {
      for (const a of actsResult.data) (grouped[a.draftFindingId] ??= []).push(a);
    }
    setReviewActions(grouped);
  }, []);

  useEffect(() => {
    (async () => {
      const modeResult = await getProviderMode();
      setMode(modeResult.ok ? modeResult.data : null);
      setBackendUp(modeResult.ok);
      await loadChunks();
      await loadReviewActions();
      const runsResult = await getAiReviewRuns();
      if (runsResult.ok && runsResult.data.length > 0) {
        setRun(runsResult.data[0]);
        const draftsResult = await getRunDraftFindings(runsResult.data[0].reviewRunId);
        setDrafts(draftsResult.ok ? draftsResult.data : []);
      }
    })();
  }, [loadChunks, loadReviewActions]);

  const handleStart = useCallback(async () => {
    setLoading(true);
    const newRun = await startAiReviewRun();
    if (newRun) {
      setBackendUp(true);
      setRun(newRun);
      const draftsResult = await getRunDraftFindings(newRun.reviewRunId);
      setDrafts(draftsResult.ok ? draftsResult.data : []);
      await loadReviewActions();
    } else {
      setBackendUp(false);
    }
    setLoading(false);
  }, [loadReviewActions]);

  const validDrafts = drafts.filter(
    (d) => d.validationStatus === "validation_passed",
  );
  const failedDrafts = drafts.filter(
    (d) => d.validationStatus !== "validation_passed",
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
          <div className="mt-4 flex flex-wrap gap-3 border-t border-slate-100 pt-4">
            <a
              href="/human-review"
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
            >
              Open the Human Review Queue
            </a>
            <a
              href="/evaluation"
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
            >
              Run evaluation scoring
            </a>
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Next steps: route these draft findings through human review, then
            score the run against the expected findings on the Evaluation page.
          </p>
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
                  {(reviewActions[d.draftFindingId]?.length ?? 0) > 0 ? (
                    <span className="badge bg-land-50 text-land-700 ring-land-600/20">
                      review recorded:{" "}
                      {reviewActions[d.draftFindingId][
                        reviewActions[d.draftFindingId].length - 1
                      ].action.replace(/_/g, " ")}
                    </span>
                  ) : (
                    <span className="badge bg-yellow-50 text-yellow-700 ring-yellow-600/20">
                      {d.status === "requires_human_review"
                        ? "Human review pending"
                        : d.status}
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

      {/* Validation failures, shown separately from valid drafts */}
      {failedDrafts.length > 0 ? (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-slate-900">
              Validation failures ({failedDrafts.length})
            </h3>
            <span className="badge bg-red-50 text-red-700 ring-red-600/20">
              Not valid review findings
            </span>
          </div>
          <p className="text-sm text-slate-600">
            These outputs failed validation or safety checks and are not usable
            as review findings until they are regenerated or reviewed. They are
            shown for transparency and are never counted as valid drafts.
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            {failedDrafts.map((d) => (
              <article
                key={d.draftFindingId}
                className="surface-card border border-red-100 p-6"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge bg-red-50 text-red-700 ring-red-600/20">
                    Failed draft
                  </span>
                  <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                    {d.checklistItemId}
                  </span>
                </div>
                <h4 className="mt-3 text-base font-semibold text-slate-900">
                  {d.title}
                </h4>
                <p className="mt-1 font-mono text-xs text-slate-400">
                  {d.draftFindingId}
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                  <StatusPill ok={false} label={`validation: ${d.validationStatus}`} />
                  <StatusPill
                    ok={d.safetyCheckStatus === "safety_check_passed"}
                    label={`safety: ${d.safetyCheckStatus}`}
                  />
                </div>
                {d.validationErrors.length > 0 ? (
                  <div className="mt-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Validation errors
                    </p>
                    <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-red-700">
                      {d.validationErrors.map((e, i) => (
                        <li key={i}>{e}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {d.sourceChunkIds.length > 0 ? (
                  <p className="mt-3 text-xs text-slate-500">
                    Source chunk ids: {d.sourceChunkIds.join(", ")}
                  </p>
                ) : null}
                <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
                  This failed draft is not usable as a review finding until it is
                  reviewed or regenerated.
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
