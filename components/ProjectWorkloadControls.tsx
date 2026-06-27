"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { PRIORITY_LABELS } from "@/lib/dashboardLabels";
import { updateProjectAssignment, updateProjectPriority } from "@/lib/api";

// Reviewer-controlled assignment and priority controls. These set workflow
// metadata only. They never change a project's engineering status and never
// approve, certify, or resolve anything. Changes require project admin access;
// the backend returns a clear permission message otherwise.
export default function ProjectWorkloadControls({
  projectId,
  currentReviewerName,
  currentPriority,
}: {
  projectId: string;
  currentReviewerName: string | null;
  currentPriority: string | null;
}) {
  const router = useRouter();
  const [reviewerName, setReviewerName] = useState(currentReviewerName ?? "");
  const [priority, setPriority] = useState(currentPriority ?? "standard");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleAssign = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await updateProjectAssignment(projectId, {
      assignedReviewerName: reviewerName.trim() || undefined,
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Could not update the assigned reviewer.");
      return;
    }
    setMessage("Assigned reviewer updated for review-support workflow.");
    router.refresh();
  };

  const handlePriority = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await updateProjectPriority(projectId, {
      reviewPriority: priority,
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Could not update the review priority.");
      return;
    }
    setMessage("Review priority updated for review-support workflow.");
    router.refresh();
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Assigned reviewer
        </label>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <input
            type="text"
            value={reviewerName}
            onChange={(e) => setReviewerName(e.target.value)}
            placeholder="Reviewer name"
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            type="button"
            onClick={handleAssign}
            disabled={busy}
            className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
          >
            Update assigned reviewer
          </button>
        </div>
      </div>

      <div>
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Review priority
        </label>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handlePriority}
            disabled={busy}
            className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
          >
            Update review priority
          </button>
        </div>
      </div>

      {error ? (
        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
          {message}
        </p>
      ) : null}
    </div>
  );
}
