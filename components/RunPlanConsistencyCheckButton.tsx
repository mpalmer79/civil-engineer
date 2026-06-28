"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { runPlanConsistencyCheck } from "@/lib/api";

// Re-runs the existing plan consistency check for a project. The check produces
// review-support findings that require reviewer confirmation. It does not perform
// final design review, verify CAD drawings, or make an engineering decision.
export default function RunPlanConsistencyCheckButton({
  projectId,
}: {
  projectId: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await runPlanConsistencyCheck(projectId);
    setBusy(false);
    if (!result.ok || !result.summary) {
      setError(result.error ?? "Could not run the plan consistency check.");
      return;
    }
    setMessage(
      `Check complete: ${result.summary.planConsistencyFindings} review-support ` +
        `finding(s), ${result.summary.requiresHumanReviewCount} need reviewer ` +
        "review.",
    );
    router.refresh();
  };

  return (
    <div>
      <button
        type="button"
        onClick={handleRun}
        disabled={busy}
        className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Running..." : "Run consistency check"}
      </button>
      {message ? (
        <p className="mt-2 rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}
