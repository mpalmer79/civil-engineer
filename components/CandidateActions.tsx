"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  dismissEvidenceCandidate,
  updateEvidenceCandidate,
} from "@/lib/api";

// Reviewer actions for an evidence candidate: edit the reviewer note and
// dismiss the candidate. Dismissal keeps the durable record and audit trail;
// it does not delete anything.
export default function CandidateActions({
  projectId,
  candidateId,
  defaultNote,
  status,
}: {
  projectId: string;
  candidateId: string;
  defaultNote: string | null;
  status: string;
}) {
  const router = useRouter();
  const [note, setNote] = useState(defaultNote ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const dismissed = status === "dismissed_by_reviewer";
  const promoted = status === "promoted_to_draft";

  const handleSaveNote = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await updateEvidenceCandidate(projectId, candidateId, {
      reviewerNote: note.trim(),
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Could not save the note.");
      return;
    }
    setMessage("Reviewer note saved.");
    router.refresh();
  };

  const handleDismiss = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await dismissEvidenceCandidate(
      projectId,
      candidateId,
      note.trim() || undefined,
    );
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Could not dismiss the candidate.");
      return;
    }
    setMessage("Candidate dismissed. The record is retained for audit.");
    router.refresh();
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Reviewer note</h3>
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        rows={2}
        disabled={dismissed}
        placeholder="Add a reviewer note for triage"
        className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50"
      />

      {error ? (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mt-3 rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
          {message}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={handleSaveNote}
          disabled={busy || dismissed}
          className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          Save note
        </button>
        {!dismissed && !promoted ? (
          <button
            type="button"
            onClick={handleDismiss}
            disabled={busy}
            className="rounded-lg border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:opacity-60"
          >
            Dismiss candidate
          </button>
        ) : null}
      </div>
    </div>
  );
}
