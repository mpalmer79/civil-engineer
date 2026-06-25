"use client";

import { useState } from "react";

// Form to record a new resubmittal package for the active review cycle.
export default function ResubmittalIntakeForm({
  disabled,
  onCreate,
}: {
  disabled?: boolean;
  onCreate: (packageName: string, submittedBy: string) => void | Promise<void>;
}) {
  const [packageName, setPackageName] = useState("");
  const [submittedBy, setSubmittedBy] = useState("Design Engineer");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async () => {
    if (!packageName.trim()) return;
    setBusy(true);
    await onCreate(packageName.trim(), submittedBy.trim() || "applicant");
    setBusy(false);
    setPackageName("");
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Record a resubmittal
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        Log a resubmittal package returned by the applicant or design engineer
        for the active review round.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Package name
          </label>
          <input
            type="text"
            value={packageName}
            onChange={(e) => setPackageName(e.target.value)}
            placeholder="Brookside Meadows resubmittal 1"
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
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
      </div>
      <button
        type="button"
        onClick={handleSubmit}
        disabled={disabled || busy || !packageName.trim()}
        className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Recording..." : "Record resubmittal"}
      </button>
    </div>
  );
}
