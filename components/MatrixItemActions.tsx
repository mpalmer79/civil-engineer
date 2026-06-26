"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  carryForwardMatrixItem,
  recordApplicantResponse,
  updateResponseMatrixItem,
  type ResponseMatrixItem,
} from "@/lib/api";

// Reviewer actions for a response matrix item: record an applicant response,
// update the reviewer follow-up status, and carry the item forward. Applicant
// responses are recorded for reviewer review. They do not finalize a review
// outcome. Carry-forward means continued review, not resolution.

const FOLLOW_UP_OPTIONS = [
  { value: "not_reviewed", label: "Not reviewed" },
  { value: "needs_reviewer_confirmation", label: "Needs reviewer confirmation" },
  { value: "needs_applicant_follow_up", label: "Needs applicant follow up" },
  { value: "evidence_updated", label: "Evidence updated" },
  { value: "reviewer_note_added", label: "Reviewer note added" },
  { value: "ready_for_reviewer_handoff", label: "Ready for reviewer handoff" },
];

const CARRY_FORWARD_OPTIONS = [
  { value: "carried_forward_for_review", label: "Carried forward for review" },
  {
    value: "carried_forward_with_updated_evidence",
    label: "Carried forward with updated evidence",
  },
  {
    value: "carried_forward_needs_applicant_response",
    label: "Carried forward needs applicant response",
  },
];

export default function MatrixItemActions({
  projectId,
  item,
}: {
  projectId: string;
  item: ResponseMatrixItem;
}) {
  const router = useRouter();
  const [responseText, setResponseText] = useState(
    item.applicantResponseText ?? "",
  );
  const [followUp, setFollowUp] = useState(item.reviewerFollowUpStatus);
  const [carryStatus, setCarryStatus] = useState("carried_forward_for_review");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const run = async (
    kind: string,
    fn: () => Promise<{ ok: boolean; error?: string }>,
    okMessage: string,
  ) => {
    setBusy(kind);
    setError(null);
    setMessage(null);
    const result = await fn();
    setBusy(null);
    if (!result.ok) {
      setError(result.error ?? "Action failed.");
      return;
    }
    setMessage(okMessage);
    router.refresh();
  };

  return (
    <div className="space-y-6">
      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Record applicant response
        </h3>
        <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          Applicant responses are recorded for reviewer review. They do not
          finalize a review outcome.
        </p>
        <textarea
          value={responseText}
          onChange={(e) => setResponseText(e.target.value)}
          rows={3}
          placeholder="Recorded applicant response text"
          className="mt-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={() =>
            run(
              "response",
              () =>
                recordApplicantResponse(projectId, item.responseMatrixItemId, {
                  applicantResponseText: responseText.trim(),
                }),
              "Applicant response recorded for reviewer review.",
            )
          }
          disabled={busy !== null || !responseText.trim()}
          className="mt-3 rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          {busy === "response" ? "Recording..." : "Record response"}
        </button>
      </div>

      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Reviewer follow-up status
        </h3>
        <select
          value={followUp}
          onChange={(e) => setFollowUp(e.target.value)}
          className="mt-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          {FOLLOW_UP_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() =>
            run(
              "followup",
              () =>
                updateResponseMatrixItem(projectId, item.responseMatrixItemId, {
                  reviewerFollowUpStatus: followUp,
                }),
              "Reviewer follow-up status updated.",
            )
          }
          disabled={busy !== null}
          className="mt-3 rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          {busy === "followup" ? "Updating..." : "Update follow-up status"}
        </button>
      </div>

      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">Carry forward</h3>
        <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          Carry-forward keeps the item under review across rounds. It is not a
          final resolution.
        </p>
        <select
          value={carryStatus}
          onChange={(e) => setCarryStatus(e.target.value)}
          className="mt-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          {CARRY_FORWARD_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() =>
            run(
              "carry",
              () =>
                carryForwardMatrixItem(projectId, item.responseMatrixItemId, {
                  carryForwardStatus: carryStatus,
                }),
              "Item carried forward for review.",
            )
          }
          disabled={busy !== null}
          className="mt-3 rounded-lg border border-water-600 px-4 py-2 text-sm font-semibold text-water-700 hover:bg-water-50 disabled:opacity-60"
        >
          {busy === "carry" ? "Carrying forward..." : "Carry forward for review"}
        </button>
      </div>

      {error ? (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
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
