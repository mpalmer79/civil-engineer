"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getHumanReviewQueue,
  getProjectReviewActions,
  getProjectChunks,
  submitReviewAction,
  type AiDraftFinding,
  type HumanReviewAction,
  type ChunkItem,
  type ReviewActionInput,
} from "@/lib/api";
import RiskBadge from "@/components/RiskBadge";

const riskFor = (level: string) =>
  level === "high" || level === "medium" || level === "low"
    ? (level as "high" | "medium" | "low")
    : "low";

// Actions allowed for a valid draft finding. There is intentionally no
// "approve" action.
const VALID_ACTIONS: { value: string; label: string }[] = [
  { value: "accepted", label: "Accept finding" },
  { value: "edited", label: "Edit finding" },
  { value: "rejected", label: "Reject finding" },
  { value: "escalated", label: "Escalate" },
  { value: "marked_unclear", label: "Mark unclear" },
  { value: "requested_more_information", label: "Request more information" },
];

// Failed drafts cannot be accepted or edited. They may only be rejected,
// escalated, or marked unclear pending regeneration.
const FAILED_ACTIONS: { value: string; label: string }[] = [
  { value: "rejected", label: "Reject finding" },
  { value: "escalated", label: "Escalate" },
  { value: "marked_unclear", label: "Mark unclear" },
];

const STATUS_LABELS: Record<string, string> = {
  requires_human_review: "Human review required",
  validation_failed: "Validation failure",
  accepted_by_reviewer: "Accepted by reviewer",
  edited_by_reviewer: "Edited by reviewer",
  rejected_by_reviewer: "Rejected by reviewer",
  escalated: "Escalated",
  marked_unclear: "Marked unclear",
  requested_more_information: "More information requested",
};

const STATUS_ORDER = [
  "requires_human_review",
  "validation_failed",
  "escalated",
  "requested_more_information",
  "marked_unclear",
  "edited_by_reviewer",
  "accepted_by_reviewer",
  "rejected_by_reviewer",
];

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

function DraftCard({
  draft,
  chunks,
  history,
  reviewerName,
  onActed,
}: {
  draft: AiDraftFinding;
  chunks: Record<string, ChunkItem>;
  history: HumanReviewAction[];
  reviewerName: string;
  onActed: () => Promise<void>;
}) {
  const isFailed = draft.validationStatus !== "validation_passed";
  const options = isFailed ? FAILED_ACTIONS : VALID_ACTIONS;
  const [action, setAction] = useState(options[0].value);
  const [note, setNote] = useState("");
  const [editTitle, setEditTitle] = useState(draft.title);
  const [editSummary, setEditSummary] = useState(draft.summary);
  const [editRec, setEditRec] = useState(draft.recommendedHumanAction);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(
    null,
  );

  const submit = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const input: ReviewActionInput = {
      action,
      reviewerName,
      reviewerNote: note,
    };
    if (action === "edited") {
      input.editedTitle = editTitle;
      input.editedSummary = editSummary;
      input.editedRecommendedAction = editRec;
    }
    const result = await submitReviewAction(draft.draftFindingId, input);
    if (result.ok) {
      setMessage({
        ok: true,
        text: `Review action recorded. New status: ${
          result.draftFinding?.status ?? "updated"
        }.`,
      });
      setNote("");
      await onActed();
    } else {
      setMessage({ ok: false, text: result.error ?? "Action failed." });
    }
    setBusy(false);
  }, [
    action,
    reviewerName,
    note,
    editTitle,
    editSummary,
    editRec,
    draft.draftFindingId,
    onActed,
  ]);

  return (
    <article className="surface-card flex flex-col p-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
          Draft finding
        </span>
        <span className="badge bg-water-50 text-water-700 ring-water-600/20">
          {draft.findingType.replace(/_/g, " ")}
        </span>
        <RiskBadge level={riskFor(draft.riskLevel)} />
      </div>
      <h4 className="mt-3 text-base font-semibold text-slate-900">
        {draft.title}
      </h4>
      <p className="mt-1 font-mono text-xs text-slate-400">
        {draft.draftFindingId} · {draft.checklistItemId}
      </p>
      <p className="mt-2 text-sm text-slate-600">{draft.summary}</p>

      <div className="mt-3 text-sm">
        <p className="font-semibold text-slate-700">Recommended human action</p>
        <p className="mt-0.5 text-slate-600">{draft.recommendedHumanAction}</p>
      </div>

      <div className="mt-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Source evidence
        </p>
        {draft.sourceChunkIds.length > 0 ? (
          <ul className="mt-1 space-y-1">
            {draft.sourceChunkIds.map((cid) => (
              <li
                key={cid}
                className="rounded-md bg-slate-50 px-2 py-1 text-xs text-slate-600"
              >
                <span className="font-mono">{cid}</span>
                {chunks[cid] ? (
                  <span className="text-slate-400">
                    {" "}
                    ({chunks[cid].fileName}
                    {chunks[cid].pageNumber != null
                      ? `, page ${chunks[cid].pageNumber}`
                      : ""}
                    )
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-1 text-xs text-slate-500">
            No source evidence cited.
          </p>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3 text-xs">
        <StatusPill
          ok={draft.validationStatus === "validation_passed"}
          label={`validation: ${draft.validationStatus}`}
        />
        <StatusPill
          ok={draft.safetyCheckStatus === "safety_check_passed"}
          label={`safety: ${draft.safetyCheckStatus}`}
        />
        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
          status: {STATUS_LABELS[draft.status] ?? draft.status}
        </span>
      </div>

      {isFailed ? (
        <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
          This draft failed validation and is not usable as a review finding
          until it is regenerated. It may be rejected, escalated, or marked
          unclear, but it cannot be accepted.
          {draft.validationErrors.length > 0 ? (
            <ul className="mt-1 list-disc pl-4">
              {draft.validationErrors.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {/* Action form */}
      <div className="mt-4 space-y-3 rounded-lg bg-slate-50 p-3">
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Review action
          </label>
          <select
            value={action}
            onChange={(e) => setAction(e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
          >
            {options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {action === "edited" ? (
          <div className="space-y-2">
            <input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              placeholder="Edited title"
              className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
            />
            <textarea
              value={editSummary}
              onChange={(e) => setEditSummary(e.target.value)}
              placeholder="Edited summary"
              rows={3}
              className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
            />
            <textarea
              value={editRec}
              onChange={(e) => setEditRec(e.target.value)}
              placeholder="Edited recommended human action"
              rows={2}
              className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
            />
          </div>
        ) : null}

        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Reviewer note (required)"
          rows={2}
          className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
        />

        <button
          type="button"
          onClick={submit}
          disabled={busy}
          className="rounded-lg bg-water-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Recording..." : "Record review action"}
        </button>

        {message ? (
          <p
            className={`rounded-md px-3 py-2 text-xs ${
              message.ok
                ? "bg-land-50 text-land-700"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            {message.text}
          </p>
        ) : null}
      </div>

      {/* Action history */}
      {history.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Action history
          </p>
          <ul className="mt-1 space-y-1">
            {history.map((a) => (
              <li
                key={a.reviewActionId}
                className="rounded-md bg-white px-2 py-1 text-xs text-slate-600 ring-1 ring-slate-100"
              >
                <span className="font-semibold text-slate-700">
                  {a.action.replace(/_/g, " ")}
                </span>{" "}
                by {a.reviewerName}: {a.previousStatus} to {a.newStatus}
                {a.reviewerNote ? (
                  <span className="block text-slate-500">{a.reviewerNote}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </article>
  );
}
