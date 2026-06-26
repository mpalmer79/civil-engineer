"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { registerResubmittalRound } from "@/lib/api";

// Register a resubmittal round. Registering a round records an applicant
// submission for reviewer review. It does not decide whether the resubmittal
// satisfies engineering requirements and does not resolve or close anything.
export default function RegisterResubmittalRound({
  projectId,
}: {
  projectId: string;
}) {
  const router = useRouter();
  const [roundLabel, setRoundLabel] = useState("");
  const [submittedBy, setSubmittedBy] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleRegister = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await registerResubmittalRound(projectId, {
      roundLabel: roundLabel.trim() || undefined,
      submittedByName: submittedBy.trim() || undefined,
    });
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not register the resubmittal round.");
      return;
    }
    setMessage("Resubmittal round registered for reviewer review.");
    setRoundLabel("");
    setSubmittedBy("");
    router.refresh();
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Register a resubmittal round
      </h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        Resubmittal review requires human confirmation. Registering a round
        records an applicant submission for reviewer review.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Round label
          </label>
          <input
            type="text"
            value={roundLabel}
            onChange={(e) => setRoundLabel(e.target.value)}
            placeholder="First resubmittal"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Submitted by
          </label>
          <input
            type="text"
            value={submittedBy}
            onChange={(e) => setSubmittedBy(e.target.value)}
            placeholder="Design firm or applicant"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
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
      <button
        type="button"
        onClick={handleRegister}
        disabled={busy}
        className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Registering..." : "Register resubmittal round"}
      </button>
    </div>
  );
}
