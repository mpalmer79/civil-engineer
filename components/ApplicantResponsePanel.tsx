"use client";

import { useState } from "react";
import type { ApplicantResponse } from "@/lib/api";

const statusStyles: Record<string, string> = {
  received: "bg-slate-100 text-slate-600",
  mapped_to_issue: "bg-water-50 text-water-700",
  needs_clarification: "bg-amber-50 text-amber-700",
  reviewer_checked: "bg-water-50 text-water-700",
  carried_forward: "bg-amber-50 text-amber-700",
};

// Shows applicant response notes for the active review cycle and lets a reviewer
// add a new response note to the selected resubmittal.
export default function ApplicantResponsePanel({
  responses,
  canAdd,
  onAdd,
}: {
  responses: ApplicantResponse[];
  canAdd: boolean;
  onAdd: (text: string, topic: string) => void | Promise<void>;
}) {
  const [text, setText] = useState("");
  const [topic, setTopic] = useState("general");
  const [busy, setBusy] = useState(false);

  const handleAdd = async () => {
    if (!text.trim()) return;
    setBusy(true);
    await onAdd(text.trim(), topic.trim() || "general");
    setBusy(false);
    setText("");
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Applicant responses
      </h3>
      {canAdd ? (
        <div className="mt-3 space-y-2">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={2}
            placeholder="Applicant response note (for example: revised the basin outlet detail per the stormwater comment)."
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="topic"
              className="w-40 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
            />
            <button
              type="button"
              onClick={handleAdd}
              disabled={busy || !text.trim()}
              className="rounded-lg bg-water-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-water-700 disabled:opacity-60"
            >
              {busy ? "Adding..." : "Add response"}
            </button>
          </div>
        </div>
      ) : (
        <p className="mt-2 text-xs text-slate-500">
          Select a resubmittal package to add applicant response notes.
        </p>
      )}

      {responses.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No applicant responses yet.</p>
      ) : (
        <ul className="mt-4 space-y-2">
          {responses.map((response) => (
            <li
              key={response.applicantResponseId}
              className="rounded-lg border border-slate-200 px-3 py-2"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {response.responseTopic}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] ${
                    statusStyles[response.status] ?? statusStyles.received
                  }`}
                >
                  {response.status.replace(/_/g, " ")}
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-700">
                {response.responseText}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
