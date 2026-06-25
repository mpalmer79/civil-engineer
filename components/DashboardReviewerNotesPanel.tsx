"use client";

import { useState } from "react";
import type { DashboardReviewerNote } from "@/lib/api";

// Reviewer notes recorded on the dashboard. Notes are review-support context and
// do not change any status or finalize anything.
export default function DashboardReviewerNotesPanel({
  notes,
  busy,
  onAdd,
}: {
  notes: DashboardReviewerNote[];
  busy: boolean;
  onAdd: (noteText: string) => void;
}) {
  const [text, setText] = useState("");

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Reviewer notes</h3>
      <div className="mt-3 flex flex-wrap items-end gap-2">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Add a review-support note for the project"
          className="min-w-[14rem] flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={() => {
            if (text.trim()) {
              onAdd(text.trim());
              setText("");
            }
          }}
          disabled={busy || !text.trim()}
          className="rounded-lg bg-water-600 px-3 py-2 text-sm font-semibold text-white transition-colors hover:bg-water-700 disabled:opacity-60"
        >
          Add note
        </button>
      </div>
      {notes.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No reviewer notes yet.</p>
      ) : (
        <ul className="mt-4 space-y-2">
          {notes.map((note) => (
            <li
              key={note.noteId}
              className="rounded-lg border border-slate-200 px-3 py-2"
            >
              <p className="text-sm text-slate-700">{note.noteText}</p>
              <p className="mt-1 text-[11px] text-slate-400">
                {note.reviewerName}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
