"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import DraftCard from "@/components/human-review/DraftCard";
import {
  STATUS_LABELS,
  STATUS_ORDER,
} from "@/components/human-review/humanReviewOptions";
import {
  getHumanReviewQueue,
  getProjectReviewActions,
  getProjectChunks,
  type AiDraftFinding,
  type HumanReviewAction,
  type ChunkItem,
} from "@/lib/api";

export default function HumanReviewClient() {
  const [drafts, setDrafts] = useState<AiDraftFinding[]>([]);
  const [actions, setActions] = useState<HumanReviewAction[]>([]);
  const [chunks, setChunks] = useState<Record<string, ChunkItem>>({});
  const [reviewerName, setReviewerName] = useState("Town Engineer");
  const [backendUp, setBackendUp] = useState(true);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    const [queueResult, actsResult] = await Promise.all([
      getHumanReviewQueue(),
      getProjectReviewActions(),
    ]);
    const queue = queueResult.ok ? queueResult.data : [];
    const acts = actsResult.ok ? actsResult.data : [];
    setDrafts(queue);
    setActions(acts);
    setBackendUp(queueResult.ok || actsResult.ok);
    setLoaded(true);
  }, []);

  useEffect(() => {
    (async () => {
      const listResult = await getProjectChunks();
      const map: Record<string, ChunkItem> = {};
      if (listResult.ok) {
        for (const c of listResult.data) map[c.chunkId] = c;
      }
      setChunks(map);
      await refresh();
    })();
  }, [refresh]);

  const actionsByDraft = useMemo(() => {
    const grouped: Record<string, HumanReviewAction[]> = {};
    for (const a of actions) (grouped[a.draftFindingId] ??= []).push(a);
    return grouped;
  }, [actions]);

  const grouped = useMemo(() => {
    const groups: Record<string, AiDraftFinding[]> = {};
    for (const d of drafts) (groups[d.status] ??= []).push(d);
    return groups;
  }, [drafts]);

  const statuses = useMemo(
    () =>
      Object.keys(grouped).sort((a, b) => {
        const ia = STATUS_ORDER.indexOf(a);
        const ib = STATUS_ORDER.indexOf(b);
        return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
      }),
    [grouped],
  );

  if (loaded && drafts.length === 0) {
    return (
      <div className="surface-card p-6">
        <p className="text-sm text-slate-600">
          No AI draft findings are available yet. Start an AI review run on the{" "}
          <a
            href="/ai-review"
            className="font-semibold text-water-700 hover:text-water-600"
          >
            AI Review
          </a>{" "}
          page, then return here to record human review actions.
        </p>
        {!backendUp ? (
          <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
            The backend is not reachable. The human review queue and review
            actions require the API. Review actions are never simulated in the
            browser.
          </p>
        ) : null}
      </div>
    );
  }

  const failedStatuses = new Set(["validation_failed"]);

  return (
    <div className="space-y-8">
      <div className="surface-card p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Human review queue
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Every AI draft finding requires human review. Record a reviewer
              action to move a draft through its review lifecycle. No action
              approves or certifies the work.
            </p>
          </div>
          <label className="text-sm">
            <span className="block font-medium text-slate-700">
              Reviewer name
            </span>
            <input
              type="text"
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
              className="mt-1 w-64 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
            />
          </label>
        </div>
      </div>

      {statuses.map((status) => {
        const items = grouped[status] ?? [];
        const isFailures = failedStatuses.has(status);
        return (
          <section key={status} className="space-y-4">
            <div className="flex items-center gap-3">
              <h3 className="text-base font-semibold text-slate-900">
                {STATUS_LABELS[status] ?? status} ({items.length})
              </h3>
              {isFailures ? (
                <span className="badge bg-red-50 text-red-700 ring-red-600/20">
                  Not usable until regenerated or reviewed
                </span>
              ) : null}
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              {items.map((d) => (
                <DraftCard
                  key={d.draftFindingId}
                  draft={d}
                  chunks={chunks}
                  history={actionsByDraft[d.draftFindingId] ?? []}
                  reviewerName={reviewerName}
                  onActed={refresh}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
