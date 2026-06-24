"use client";

import { useCallback, useState } from "react";
import {
  createReviewPacketReviewerAction,
  type ReviewPacketItem,
} from "@/lib/api";

// Review packet reviewer actions. There is intentionally no approve action.
const ACTIONS: { value: string; label: string }[] = [
  { value: "reviewer_checked", label: "Reviewer checked" },
  { value: "needs_follow_up", label: "Needs follow up" },
  { value: "needs_more_information", label: "Needs more information" },
  { value: "excluded_from_packet", label: "Exclude from packet" },
];

export default function ReviewPacketActionPanel({
  packetId,
  item,
  reviewerName,
  onReviewerNameChange,
  onItemUpdated,
}: {
  packetId: string;
  item: ReviewPacketItem | null;
  reviewerName: string;
  onReviewerNameChange: (name: string) => void;
  onItemUpdated: (item: ReviewPacketItem) => void;
}) {
  const [action, setAction] = useState(ACTIONS[0].value);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(
    null,
  );

  const submit = useCallback(async () => {
    if (!item) return;
    setBusy(true);
    setMessage(null);
    const result = await createReviewPacketReviewerAction(packetId, item.itemId, {
      actionType: action,
      reviewerNote: note,
      reviewerName,
    });
    if (result.ok && result.item) {
      setMessage({
        ok: true,
        text: `Action recorded. New status: ${result.item.reviewerStatus.replace(
          /_/g,
          " ",
        )}.`,
      });
      setNote("");
      onItemUpdated(result.item);
    } else {
      setMessage({ ok: false, text: result.error ?? "Action failed." });
    }
    setBusy(false);
  }, [item, packetId, action, note, reviewerName, onItemUpdated]);

  if (!item) return null;

  return (
    <div className="surface-card p-6">
      <h3 className="text-base font-semibold text-slate-900">Reviewer action</h3>
      <p className="mt-1 text-xs text-slate-500">
        Record a review-support action on this item. No action approves,
        certifies, verifies, or validates anything.
      </p>

      <label className="mt-4 block text-sm">
        <span className="font-medium text-slate-700">Reviewer name</span>
        <input
          type="text"
          value={reviewerName}
          onChange={(e) => onReviewerNameChange(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm sm:w-64"
        />
      </label>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Action
        </label>
        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
        >
          {ACTIONS.map((a) => (
            <option key={a.value} value={a.value}>
              {a.label}
            </option>
          ))}
        </select>
      </div>

      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Reviewer note (required)"
        rows={2}
        className="mt-3 w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
      />

      <button
        type="button"
        onClick={submit}
        disabled={busy}
        className="mt-3 rounded-lg bg-water-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Recording..." : "Record action"}
      </button>

      {message ? (
        <p
          className={`mt-3 rounded-md px-3 py-2 text-xs ${
            message.ok ? "bg-land-50 text-land-700" : "bg-amber-50 text-amber-700"
          }`}
        >
          {message.text}
        </p>
      ) : null}
    </div>
  );
}
