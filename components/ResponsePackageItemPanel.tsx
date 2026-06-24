"use client";

import { useState } from "react";
import {
  addResponsePackageNote,
  updateResponseItemStatus,
  type ResponsePackageItem,
} from "@/lib/api";

// Manual response item status transitions. draft is the seeded status and is
// not a manual target. There is no approve status.
const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "included", label: "Include in response" },
  { value: "excluded", label: "Exclude from response" },
  { value: "needs_revision", label: "Needs revision" },
  { value: "reviewer_checked", label: "Reviewer checked" },
];

// Detail and reviewer controls for a selected response item: status updates and
// reviewer notes. Every action stays under human review.
export default function ResponsePackageItemPanel({
  packageId,
  item,
  reviewerName,
  onReviewerNameChange,
  onItemUpdated,
}: {
  packageId: string;
  item: ResponsePackageItem | null;
  reviewerName: string;
  onReviewerNameChange: (name: string) => void;
  onItemUpdated: (item: ResponsePackageItem) => void;
}) {
  const [newStatus, setNewStatus] = useState("included");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (!item) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Select a response item to manage its status and notes.
      </div>
    );
  }

  const inputClass =
    "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-water-500 focus:outline-none focus:ring-1 focus:ring-water-500";

  const handleStatus = async () => {
    setBusy(true);
    setMessage(null);
    const result = await updateResponseItemStatus(
      packageId,
      item.itemId,
      newStatus,
      note || undefined,
      reviewerName,
    );
    if (result.ok && result.item) {
      onItemUpdated(result.item);
      setNote("");
      setMessage("Item status updated.");
    } else {
      setMessage(result.error ?? "Could not update the item status.");
    }
    setBusy(false);
  };

  const handleNote = async () => {
    setBusy(true);
    setMessage(null);
    const result = await addResponsePackageNote(
      packageId,
      item.itemId,
      note,
      reviewerName,
    );
    if (result.ok) {
      setNote("");
      setMessage("Reviewer note recorded.");
    } else {
      setMessage(result.error ?? "Could not add the note.");
    }
    setBusy(false);
  };

  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">{item.title}</h3>
        <span className="text-xs text-slate-500">severity: {item.severity}</span>
      </div>
      <p className="mt-2 text-sm text-slate-600">{item.draftText}</p>
      {item.reviewerNote ? (
        <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Latest reviewer note
          </p>
          <p className="mt-1 text-sm text-slate-700">{item.reviewerNote}</p>
        </div>
      ) : null}

      <div className="mt-4 space-y-3">
        <label className="block text-sm font-medium text-slate-700">
          Reviewer name
          <input
            value={reviewerName}
            onChange={(e) => onReviewerNameChange(e.target.value)}
            className={inputClass}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          New status
          <select
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
            className={inputClass}
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Reviewer note (optional for status, required for a standalone note)
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            className={inputClass}
          />
        </label>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleStatus}
            disabled={busy}
            className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Saving..." : "Update status"}
          </button>
          <button
            type="button"
            onClick={handleNote}
            disabled={busy || !note.trim()}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            Add note only
          </button>
        </div>
        {message ? (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
            {message}
          </p>
        ) : null}
      </div>
    </div>
  );
}
