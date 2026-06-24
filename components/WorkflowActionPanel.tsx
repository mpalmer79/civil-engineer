"use client";

import { useState } from "react";
import {
  addWorkflowNote,
  createWorkflowFollowUp,
  updateWorkflowItemStatus,
  type WorkflowItem,
} from "@/lib/api";

// Manual status transitions a reviewer may apply on the board. draft is the
// seeded status and is not a manual transition target, so it is not offered
// here. There is intentionally no approve action.
const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "needs_triage", label: "Start triage" },
  { value: "needs_more_information", label: "Request more information" },
  { value: "reviewer_checked", label: "Mark reviewer checked" },
  { value: "excluded_from_packet", label: "Exclude from packet" },
  { value: "ready_for_handoff", label: "Mark ready for handoff" },
];

type Mode = "status" | "note" | "follow_up";

// Reviewer action form for a workflow item: move its board status, add a note,
// or open a follow-up request. Every action stays under human control and none
// approves, certifies, verifies, or validates the work.
export default function WorkflowActionPanel({
  item,
  reviewerName,
  onReviewerNameChange,
  onChanged,
}: {
  item: WorkflowItem | null;
  reviewerName: string;
  onReviewerNameChange: (name: string) => void;
  onChanged: () => void;
}) {
  const [mode, setMode] = useState<Mode>("status");
  const [newStatus, setNewStatus] = useState("needs_triage");
  const [targetDate, setTargetDate] = useState("");
  const [note, setNote] = useState("");
  const [requestedFrom, setRequestedFrom] = useState("Applicant");
  const [requestReason, setRequestReason] = useState("");
  const [requestedInformation, setRequestedInformation] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (!item) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Select a workflow item to record a reviewer action.
      </div>
    );
  }

  const reset = () => {
    setNote("");
    setRequestReason("");
    setRequestedInformation("");
    setTargetDate("");
  };

  const handleStatus = async () => {
    setBusy(true);
    setMessage(null);
    const result = await updateWorkflowItemStatus(
      item.workflowItemId,
      newStatus,
      note || undefined,
      reviewerName,
      targetDate || undefined,
    );
    if (result.ok) {
      setMessage("Workflow item status updated.");
      reset();
      onChanged();
    } else {
      setMessage(result.error ?? "Could not update the status.");
    }
    setBusy(false);
  };

  const handleNote = async () => {
    setBusy(true);
    setMessage(null);
    const result = await addWorkflowNote(item.workflowItemId, note, reviewerName);
    if (result.ok) {
      setMessage("Reviewer note recorded.");
      reset();
      onChanged();
    } else {
      setMessage(result.error ?? "Could not add the note.");
    }
    setBusy(false);
  };

  const handleFollowUp = async () => {
    setBusy(true);
    setMessage(null);
    const result = await createWorkflowFollowUp(item.workflowItemId, {
      requestedFrom,
      requestReason,
      requestedInformation,
      reviewerName,
      targetDate: targetDate || undefined,
    });
    if (result.ok) {
      setMessage("Follow-up request opened. Item moved to needs follow-up.");
      reset();
      onChanged();
    } else {
      setMessage(result.error ?? "Could not open the follow-up request.");
    }
    setBusy(false);
  };

  const inputClass =
    "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-water-500 focus:outline-none focus:ring-1 focus:ring-water-500";

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Reviewer action</h3>
      <div className="mt-3 flex flex-wrap gap-2">
        {(
          [
            ["status", "Change status"],
            ["note", "Add note"],
            ["follow_up", "Request follow-up"],
          ] as [Mode, string][]
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            onClick={() => setMode(value)}
            className={`rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors ${
              mode === value
                ? "bg-water-600 text-white"
                : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-4 space-y-3">
        <label className="block text-sm font-medium text-slate-700">
          Reviewer name
          <input
            value={reviewerName}
            onChange={(e) => onReviewerNameChange(e.target.value)}
            className={inputClass}
          />
        </label>

        {mode === "status" ? (
          <>
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
              Target date (optional)
              <input
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                placeholder="2026-07-15"
                className={inputClass}
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Reviewer note (optional)
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={2}
                className={inputClass}
              />
            </label>
            <button
              type="button"
              onClick={handleStatus}
              disabled={busy}
              className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
            >
              {busy ? "Saving..." : "Update status"}
            </button>
          </>
        ) : null}

        {mode === "note" ? (
          <>
            <label className="block text-sm font-medium text-slate-700">
              Reviewer note
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={3}
                className={inputClass}
              />
            </label>
            <button
              type="button"
              onClick={handleNote}
              disabled={busy || !note.trim()}
              className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
            >
              {busy ? "Saving..." : "Add note"}
            </button>
          </>
        ) : null}

        {mode === "follow_up" ? (
          <>
            <label className="block text-sm font-medium text-slate-700">
              Requested from
              <input
                value={requestedFrom}
                onChange={(e) => setRequestedFrom(e.target.value)}
                className={inputClass}
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Reason
              <textarea
                value={requestReason}
                onChange={(e) => setRequestReason(e.target.value)}
                rows={2}
                className={inputClass}
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Information requested
              <textarea
                value={requestedInformation}
                onChange={(e) => setRequestedInformation(e.target.value)}
                rows={2}
                className={inputClass}
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Target date (optional)
              <input
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                placeholder="2026-07-15"
                className={inputClass}
              />
            </label>
            <button
              type="button"
              onClick={handleFollowUp}
              disabled={
                busy ||
                !requestReason.trim() ||
                !requestedInformation.trim()
              }
              className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
            >
              {busy ? "Saving..." : "Open follow-up request"}
            </button>
          </>
        ) : null}

        {message ? (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
            {message}
          </p>
        ) : null}
      </div>
    </div>
  );
}
