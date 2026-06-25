"use client";

import { useState } from "react";
import type { ResponseResolutionRecord } from "@/lib/api";

const RESOLUTION_STATUSES = [
  "addressed_for_review",
  "still_open",
  "needs_more_information",
  "carried_forward",
  "reviewer_checked",
  "excluded_from_cycle",
];

const statusStyles: Record<string, string> = {
  addressed_for_review: "bg-water-50 text-water-700",
  still_open: "bg-amber-50 text-amber-700",
  needs_more_information: "bg-amber-50 text-amber-700",
  carried_forward: "bg-amber-50 text-amber-700",
  reviewer_checked: "bg-water-50 text-water-700",
  excluded_from_cycle: "bg-slate-100 text-slate-500",
};

// Lets a reviewer record and update review-support resolution statuses. None of
// these is a final decision: addressed_for_review means an item appears
// addressed for human review, never resolved, approved, or certified.
export default function ResponseResolutionPanel({
  records,
  busy,
  onCreate,
  onUpdateStatus,
}: {
  records: ResponseResolutionRecord[];
  busy: boolean;
  onCreate: (status: string, reviewerNote: string) => void;
  onUpdateStatus: (resolutionRecordId: string, status: string) => void;
}) {
  const [status, setStatus] = useState("addressed_for_review");
  const [note, setNote] = useState("");

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Response resolution
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        Record whether an item appears addressed for review, is still open, needs
        more information, should be carried forward, or has been reviewer checked.
        These are review-support statuses, not final decisions.
      </p>
      <div className="mt-3 flex flex-wrap items-end gap-2">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Status
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 px-2 py-2 text-sm"
          >
            {RESOLUTION_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>
        <input
          type="text"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Reviewer note"
          className="min-w-[12rem] flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={() => {
            onCreate(status, note);
            setNote("");
          }}
          disabled={busy}
          className="rounded-lg bg-water-600 px-3 py-2 text-sm font-semibold text-white transition-colors hover:bg-water-700 disabled:opacity-60"
        >
          Add record
        </button>
      </div>

      {records.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No resolution records yet.
        </p>
      ) : (
        <ul className="mt-4 space-y-2">
          {records.map((record) => (
            <li
              key={record.resolutionRecordId}
              className="rounded-lg border border-slate-200 px-3 py-2"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] ${
                    statusStyles[record.status] ?? statusStyles.still_open
                  }`}
                >
                  {record.status.replace(/_/g, " ")}
                </span>
                <select
                  value={record.status}
                  onChange={(e) =>
                    onUpdateStatus(record.resolutionRecordId, e.target.value)
                  }
                  className="rounded-md border border-slate-300 px-2 py-1 text-xs"
                >
                  {RESOLUTION_STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>
              {record.reviewerNote ? (
                <p className="mt-1 text-xs text-slate-600">
                  {record.reviewerNote}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
