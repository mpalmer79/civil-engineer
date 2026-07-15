"use client";

import { useCallback, useState } from "react";

import {
  FAILED_ACTIONS,
  riskFor,
  STATUS_LABELS,
  VALID_ACTIONS,
} from "@/components/human-review/humanReviewOptions";
import RiskBadge from "@/components/RiskBadge";
import {
  submitReviewAction,
  type AiDraftFinding,
  type ChunkItem,
  type HumanReviewAction,
  type ReviewActionInput,
} from "@/lib/api";

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

// A single AI draft finding awaiting human review. Records reviewer actions;
// no action approves or certifies the work.
export default function DraftCard({
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
