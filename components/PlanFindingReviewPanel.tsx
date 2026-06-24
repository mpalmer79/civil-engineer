"use client";

import { useCallback, useState } from "react";
import {
  createPlanConsistencyReviewAction,
  type PlanConsistencyFinding,
  type PlanSheetHotspot,
} from "@/lib/api";
import PlanStatusBadge from "@/components/PlanStatusBadge";
import RiskBadge from "@/components/RiskBadge";

const riskFor = (level: string) =>
  level === "high" || level === "medium" || level === "low"
    ? (level as "high" | "medium" | "low")
    : "low";

// Plan consistency review actions. There is intentionally no approve action.
const ACTIONS: { value: string; label: string }[] = [
  { value: "needs_follow_up", label: "Needs follow up" },
  { value: "reviewer_confirmed", label: "Reviewer confirmed" },
  { value: "not_applicable", label: "Not applicable" },
  { value: "needs_more_information", label: "Needs more information" },
];

export default function PlanFindingReviewPanel({
  hotspot,
  findings,
  reviewerName,
  onReviewerNameChange,
  onActionRecorded,
}: {
  hotspot: PlanSheetHotspot | null;
  findings: PlanConsistencyFinding[];
  reviewerName: string;
  onReviewerNameChange: (name: string) => void;
  onActionRecorded: (updated: PlanConsistencyFinding) => void;
}) {
  if (!hotspot) return null;

  const related = findings.filter((f) =>
    hotspot.relatedPlanFindingIds.includes(f.planFindingId),
  );

  return (
    <div className="surface-card p-6">
      <h3 className="text-base font-semibold text-slate-900">
        Plan consistency findings
      </h3>
      <p className="mt-1 text-xs text-slate-500">
        Record a review-support action on a finding tied to this hotspot. No
        action approves a plan, certifies compliance, or verifies CAD.
      </p>

      <label className="mt-4 block text-sm">
        <span className="font-medium text-slate-700">Reviewer name</span>
        <input
          type="text"
          value={reviewerName}
          onChange={(e) => onReviewerNameChange(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm sm:w-64"
        />
      </label>

      {related.length > 0 ? (
        <div className="mt-4 space-y-4">
          {related.map((f) => (
            <FindingReviewCard
              key={f.planFindingId}
              finding={f}
              reviewerName={reviewerName}
              onActionRecorded={onActionRecorded}
            />
          ))}
        </div>
      ) : (
        <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
          This hotspot is not tied to a plan consistency finding. It is a
          review-support annotation for reviewer confirmation.
        </p>
      )}
    </div>
  );
}

function FindingReviewCard({
  finding,
  reviewerName,
  onActionRecorded,
}: {
  finding: PlanConsistencyFinding;
  reviewerName: string;
  onActionRecorded: (updated: PlanConsistencyFinding) => void;
}) {
  const [action, setAction] = useState(ACTIONS[0].value);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(
    null,
  );

  const submit = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await createPlanConsistencyReviewAction(
      finding.planFindingId,
      { action, reviewerName, reviewerNote: note },
    );
    if (result.ok && result.finding) {
      setMessage({
        ok: true,
        text: `Review action recorded. New status: ${result.finding.status.replace(
          /_/g,
          " ",
        )}.`,
      });
      setNote("");
      onActionRecorded(result.finding);
    } else {
      setMessage({ ok: false, text: result.error ?? "Action failed." });
    }
    setBusy(false);
  }, [action, note, reviewerName, finding.planFindingId, onActionRecorded]);

  return (
    <article className="rounded-lg border border-slate-200 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <PlanStatusBadge status={finding.findingType} />
        <RiskBadge level={riskFor(finding.riskLevel)} />
        <PlanStatusBadge status={finding.status} />
      </div>
      <h4 className="mt-2 text-sm font-semibold text-slate-900">
        {finding.title}
      </h4>
      <p className="mt-1 text-sm text-slate-600">{finding.summary}</p>
      <p className="mt-2 text-xs text-slate-500">
        <span className="font-semibold text-slate-600">
          Recommended human action:{" "}
        </span>
        {finding.recommendedHumanAction}
      </p>

      <div className="mt-3 space-y-2 rounded-md bg-slate-50 p-3">
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Review action
          </label>
          <select
            value={action}
            onChange={(e) => setAction(e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
          >
            {ACTIONS.map((a) => (
              <option key={a.value} value={a.value}>
                {a.label}
              </option>
            ))}
          </select>
        </div>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Reviewer note (required)"
          rows={2}
          className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
        />
        <button
          type="button"
          onClick={submit}
          disabled={busy}
          className="rounded-lg bg-water-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Recording..." : "Record review action"}
        </button>
        {message ? (
          <p
            className={`rounded-md px-3 py-2 text-xs ${
              message.ok
                ? "bg-land-50 text-land-700"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            {message.text}
          </p>
        ) : null}
      </div>
    </article>
  );
}
