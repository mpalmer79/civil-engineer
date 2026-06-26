"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  linkDocumentToResubmittalRound,
  type ResubmittalRound,
} from "@/lib/api";

// Link a document to a resubmittal round. Linking organizes a received document
// for reviewer review under a resubmittal round. It does not decide whether the
// resubmittal satisfies engineering requirements and does not resolve or close
// anything.
export default function LinkDocumentToResubmittalRound({
  projectId,
  documentId,
  rounds,
}: {
  projectId: string;
  documentId: string;
  rounds: ResubmittalRound[];
}) {
  const router = useRouter();
  const [roundId, setRoundId] = useState(
    rounds.length > 0 ? rounds[0].resubmittalRoundId : "",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleLink = async () => {
    if (!roundId) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await linkDocumentToResubmittalRound(
      projectId,
      roundId,
      documentId,
    );
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not link the document to the round.");
      return;
    }
    setMessage("Document linked to the resubmittal round for reviewer review.");
    router.refresh();
  };

  if (rounds.length === 0) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Link to resubmittal round
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          No resubmittal round exists for this project yet. Register one from the{" "}
          <a
            href={`/projects/${projectId}/resubmittals`}
            className="text-water-700 hover:underline"
          >
            resubmittal rounds page
          </a>{" "}
          first, then link this document for reviewer review.
        </p>
      </div>
    );
  }

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Link to resubmittal round
      </h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        Linking this document to a resubmittal round organizes it for reviewer
        review. It does not finalize a review outcome.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <select
          value={roundId}
          onChange={(e) => setRoundId(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          {rounds.map((r) => (
            <option key={r.resubmittalRoundId} value={r.resubmittalRoundId}>
              Round {r.roundNumber}: {r.roundLabel}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleLink}
          disabled={busy || !roundId}
          className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Linking..." : "Link to resubmittal round"}
        </button>
      </div>
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
    </div>
  );
}
