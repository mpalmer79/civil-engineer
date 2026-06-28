"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  createPlanConsistencyReviewAction,
  type PlanConsistencyReviewAction,
} from "@/lib/api";
import { humanizeStatus } from "@/components/StatusChip";

// Reviewer-controlled review actions for a single plan consistency finding plus
// the recorded action history. An action records the reviewer's decision to
// follow up, confirm as reviewed, mark not applicable, or request more
// information. There is no approve action. None of these finalize a review or
// make an engineering decision.
const ACTIONS: { value: string; label: string }[] = [
  { value: "needs_follow_up", label: "Needs follow-up" },
  { value: "reviewer_confirmed", label: "Reviewer confirmed (reviewed)" },
  { value: "not_applicable", label: "Not applicable" },
  { value: "needs_more_information", label: "Needs more information" },
];

export default function PlanConsistencyFindingActions({
  planFindingId,
  history,
}: {
  planFindingId: string;
  history: PlanConsistencyReviewAction[];
}) {
  const router = useRouter();
  const [action, setAction] = useState("needs_follow_up");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRecord = async () => {
    setBusy(true);
    setError(null);
    const result = await createPlanConsistencyReviewAction(planFindingId, {
      action,
      reviewerName: "Reviewer",
      reviewerNote: note,
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Could not record the review action.");
      return;
    }
    setNote("");
    router.refresh();
  };

  return (
    <div className="mt-3 border-t border-slate-100 pt-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Reviewer action
      </p>
      <div className="mt-1 flex flex-wrap items-end gap-2">
        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="rounded-md border border-slate-300 px-2 py-1.5 text-xs"
        >
          {ACTIONS.map((a) => (
            <option key={a.value} value={a.value}>
              {a.label}
            </option>
          ))}
        </select>
        <input
          type="text"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Reviewer note (optional)"
          className="min-w-[12rem] flex-1 rounded-md border border-slate-300 px-2 py-1.5 text-xs"
        />
        <button
          type="button"
          onClick={handleRecord}
          disabled={busy}
          className="rounded-md bg-water-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Recording..." : "Record action"}
        </button>
      </div>
      {error ? (
        <p className="mt-1 text-xs text-red-700">{error}</p>
      ) : null}
      {history.length > 0 ? (
        <div className="mt-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Action history
          </p>
          <ul className="mt-1 space-y-1">
            {history.map((a) => (
              <li key={a.reviewActionId} className="text-xs text-slate-600">
                <span className="font-medium text-slate-700">
                  {humanizeStatus(a.action)}
                </span>{" "}
                by {a.reviewerName}
                {a.reviewerNote ? `: ${a.reviewerNote}` : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
