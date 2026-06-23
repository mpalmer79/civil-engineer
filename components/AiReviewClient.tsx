"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getProviderMode,
  getAiReviewRuns,
  getRunDraftFindings,
  startAiReviewRun,
  getProjectChunks,
  type ProviderModeInfo,
  type AiReviewRun,
  type AiDraftFinding,
  type ChunkItem,
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
  const [loading, setLoading] = useState(false);
  const [backendUp, setBackendUp] = useState(true);

  const loadChunks = useCallback(async () => {
    const list = await getProjectChunks();
    const map: Record<string, ChunkItem> = {};
    for (const c of list) map[c.chunkId] = c;
    setChunks(map);
  }, []);

  useEffect(() => {
    (async () => {
      const m = await getProviderMode();
      setMode(m);
      setBackendUp(m !== null);
      await loadChunks();
      const runs = await getAiReviewRuns();
      if (runs.length > 0) {
        setRun(runs[0]);
        setDrafts(await getRunDraftFindings(runs[0].reviewRunId));
      }
    })();
  }, [loadChunks]);

  const handleStart = useCallback(async () => {
    setLoading(true);
    const newRun = await startAiReviewRun();
    if (newRun) {
      setBackendUp(true);
      setRun(newRun);
      setDrafts(await getRunDraftFindings(newRun.reviewRunId));
    } else {
      setBackendUp(false);
    }
    setLoading(false);
  }, []);

  const validDrafts = drafts.filter(
    (d) => d.validationStatus === "validation_passed",
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
                  <span className="badge bg-yellow-50 text-yellow-700 ring-yellow-600/20">
                    {d.status === "requires_human_review"
                      ? "Human reviewer action required"
                      : d.status}
                  </span>
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
