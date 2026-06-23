"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getHumanReviewQueue,
  submitReviewAction,
  type HumanReviewQueue,
  type HumanReviewQueueItem,
  type ReviewActionInput,
} from "@/lib/api";
import RiskBadge from "@/components/RiskBadge";

const ACTIONS: { value: string; label: string }[] = [
  { value: "accepted", label: "Accept finding" },
  { value: "edited", label: "Edit finding" },
  { value: "rejected", label: "Reject finding" },
  { value: "escalated", label: "Escalate" },
  { value: "marked_unclear", label: "Mark unclear" },
  { value: "requested_more_information", label: "Request more information" },
];

const riskFor = (level: string) =>
  level === "high" || level === "medium" || level === "low"
    ? (level as "high" | "medium" | "low")
    : "low";

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`badge ${
        ok
          ? "bg-land-50 text-land-700 ring-land-600/20"
          : "bg-red-50 text-red-700 ring-red-600/20"
      }`}
    >
      {label}
    </span>
  );
}

export default function HumanReviewClient() {
  const [queue, setQueue] = useState<HumanReviewQueue | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [backendUp, setBackendUp] = useState(true);

  const reload = useCallback(async () => {
    const q = await getHumanReviewQueue();
    setQueue(q);
    setBackendUp(q !== null);
    setLoaded(true);
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  if (!loaded) {
    return (
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
        Loading the human review queue.
      </p>
    );
  }

  if (!backendUp || !queue) {
    return (
      <div className="surface-card p-6">
        <h2 className="text-lg font-semibold text-slate-900">
          Human review queue
        </h2>
        <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
          The backend is not reachable. Start the API and run an AI review to
          populate the queue. Review actions are recorded in the backend and are
          never faked in frontend-only mode.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Counter label="Needs human review" value={queue.needsReviewCount} accent="amber" />
        <Counter label="Review action recorded" value={queue.reviewedCount} accent="land" />
        <Counter
          label="Validation failures"
          value={queue.validationFailureCount}
          accent="red"
        />
      </div>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Draft findings that need human review ({queue.needsReviewCount})
        </h2>
        {queue.needsReview.length === 0 ? (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
            No draft findings are waiting for review. Run an AI review on the AI
            Review page to generate draft findings.
          </p>
        ) : (
          <div className="space-y-4">
            {queue.needsReview.map((item) => (
              <ReviewableCard
                key={item.draftFinding.draftFindingId}
                item={item}
                onActionDone={reload}
              />
            ))}
          </div>
        )}
      </section>

      {queue.reviewed.length > 0 ? (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">
            Reviewed draft findings ({queue.reviewedCount})
          </h2>
          <div className="space-y-4">
            {queue.reviewed.map((item) => (
              <ReviewedCard key={item.draftFinding.draftFindingId} item={item} />
            ))}
          </div>
        </section>
      ) : null}

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Validation failures ({queue.validationFailureCount})
        </h2>
        <p className="text-sm text-slate-600">
          These draft outputs failed validation or safety checks. They are shown
          as failures only and are not usable review findings until they are
          regenerated. A failed draft can be rejected, escalated, marked unclear,
          or have more information requested, but it cannot be accepted.
        </p>
        {queue.validationFailures.length === 0 ? (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
            No validation failures in the current draft findings.
          </p>
        ) : (
          <div className="space-y-4">
            {queue.validationFailures.map((item) => (
              <FailedReviewCard
                key={item.draftFinding.draftFindingId}
                item={item}
                onActionDone={reload}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Counter({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: "amber" | "land" | "red";
}) {
  const ring =
    accent === "land"
      ? "ring-land-600/20"
      : accent === "red"
        ? "ring-red-600/20"
        : "ring-amber-600/20";
  return (
    <div className={`surface-card p-4 ring-1 ${ring}`}>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </div>
    </div>
  );
}

function DraftHeader({ item }: { item: HumanReviewQueueItem }) {
  const d = item.draftFinding;
  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
          Draft finding
        </span>
        <span className="badge bg-water-50 text-water-700 ring-water-600/20">
          {d.findingType.replace(/_/g, " ")}
        </span>
        <RiskBadge level={riskFor(d.riskLevel)} />
        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
          {item.checklistItemId}
        </span>
      </div>
      <h3 className="mt-3 text-base font-semibold text-slate-900">{d.title}</h3>
      <p className="mt-2 text-sm text-slate-600">{d.summary}</p>
      <div className="mt-3 text-sm">
        <p className="font-semibold text-slate-700">Recommended human action</p>
        <p className="mt-0.5 text-slate-600">{d.recommendedHumanAction}</p>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <StatusPill
          ok={d.validationStatus === "validation_passed"}
          label={`validation: ${d.validationStatus}`}
        />
        <StatusPill
          ok={d.safetyCheckStatus === "safety_check_passed"}
          label={`safety: ${d.safetyCheckStatus}`}
        />
        <span className="font-mono text-slate-400">
          confidence {Math.round(d.confidence * 100)}%
        </span>
        <span className="font-mono text-slate-400">
          evidence: {d.sourceChunkIds.join(", ") || "none"}
        </span>
      </div>
    </>
  );
}

function ActionHistory({ item }: { item: HumanReviewQueueItem }) {
  if (item.reviewActions.length === 0) return null;
  return (
    <div className="mt-4 border-t border-slate-100 pt-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Action history
      </p>
      <ul className="mt-2 space-y-1 text-xs text-slate-600">
        {item.reviewActions.map((a) => (
          <li key={a.reviewActionId} className="rounded-md bg-slate-50 px-2 py-1">
            <span className="font-semibold">{a.action.replace(/_/g, " ")}</span>{" "}
            by {a.reviewerName}: {a.previousStatus} to {a.newStatus}
            {a.reviewerNote ? (
              <span className="block text-slate-500">{a.reviewerNote}</span>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ReviewableCard({
  item,
  onActionDone,
  failedOnly = false,
}: {
  item: HumanReviewQueueItem;
  onActionDone: () => void;
  failedOnly?: boolean;
}) {
  const [action, setAction] = useState(failedOnly ? "rejected" : "accepted");
  const [reviewerName, setReviewerName] = useState("Town Engineer");
  const [note, setNote] = useState("");
  const [editedTitle, setEditedTitle] = useState(item.draftFinding.title);
  const [editedSummary, setEditedSummary] = useState(item.draftFinding.summary);
  const [editedAction, setEditedAction] = useState(
    item.draftFinding.recommendedHumanAction,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const available = failedOnly
    ? ACTIONS.filter((a) => a.value !== "accepted" && a.value !== "edited")
    : ACTIONS;

  const handleSubmit = useCallback(async () => {
    setBusy(true);
    setError(null);
    const input: ReviewActionInput = {
      action,
      reviewerName,
      reviewerNote: note,
    };
    if (action === "edited") {
      input.editedTitle = editedTitle;
      input.editedSummary = editedSummary;
      input.editedRecommendedAction = editedAction;
    }
    const result = await submitReviewAction(
      item.draftFinding.draftFindingId,
      input,
    );
    if (result.ok) {
      onActionDone();
    } else {
      setError(result.message);
      setBusy(false);
    }
  }, [
    action,
    reviewerName,
    note,
    editedTitle,
    editedSummary,
    editedAction,
    item.draftFinding.draftFindingId,
    onActionDone,
  ]);

  return (
    <article className="surface-card p-6">
      <DraftHeader item={item} />
      <ActionHistory item={item} />

      <div className="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2">
        <label className="text-sm">
          <span className="font-semibold text-slate-700">Review action</span>
          <select
            value={action}
            onChange={(e) => setAction(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          >
            {available.map((a) => (
              <option key={a.value} value={a.value}>
                {a.label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="font-semibold text-slate-700">Reviewer name</span>
          <input
            value={reviewerName}
            onChange={(e) => setReviewerName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          />
        </label>
      </div>

      <label className="mt-3 block text-sm">
        <span className="font-semibold text-slate-700">Reviewer note</span>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={2}
          placeholder="Required: explain the decision for the audit record."
          className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        />
      </label>

      {action === "edited" ? (
        <div className="mt-3 space-y-3 rounded-md bg-slate-50 p-3">
          <label className="block text-sm">
            <span className="font-semibold text-slate-700">Edited title</span>
            <input
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            />
          </label>
          <label className="block text-sm">
            <span className="font-semibold text-slate-700">Edited summary</span>
            <textarea
              value={editedSummary}
              onChange={(e) => setEditedSummary(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            />
          </label>
          <label className="block text-sm">
            <span className="font-semibold text-slate-700">
              Edited recommended action
            </span>
            <textarea
              value={editedAction}
              onChange={(e) => setEditedAction(e.target.value)}
              rows={2}
              className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            />
          </label>
          <p className="text-xs text-slate-500">
            Edited text is checked for prohibited final-decision wording before it
            is saved. Words such as approved, certified, compliant, or safe are
            rejected.
          </p>
        </div>
      ) : null}

      {error ? (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <div className="mt-4">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={busy}
          className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Recording action..." : "Record review action"}
        </button>
      </div>
    </article>
  );
}

function FailedReviewCard({
  item,
  onActionDone,
}: {
  item: HumanReviewQueueItem;
  onActionDone: () => void;
}) {
  const d = item.draftFinding;
  return (
    <article className="surface-card border-l-4 border-red-300 p-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="badge bg-red-50 text-red-700 ring-red-600/20">
          Validation failure
        </span>
        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
          {item.checklistItemId}
        </span>
        <span className="font-mono text-xs text-slate-400">
          {d.draftFindingId}
        </span>
      </div>
      <h3 className="mt-3 text-base font-semibold text-slate-900">{d.title}</h3>
      <p className="mt-2 text-sm font-medium text-red-700">
        This failed draft is not a usable review finding until it is reviewed or
        regenerated.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <StatusPill ok={false} label={`validation: ${d.validationStatus}`} />
        <StatusPill
          ok={d.safetyCheckStatus === "safety_check_passed"}
          label={`safety: ${d.safetyCheckStatus}`}
        />
        <span className="font-mono text-slate-400">
          evidence: {d.sourceChunkIds.join(", ") || "none"}
        </span>
      </div>
      {d.validationErrors.length > 0 ? (
        <ul className="mt-3 space-y-1">
          {d.validationErrors.map((err, i) => (
            <li
              key={i}
              className="rounded-md bg-red-50 px-2 py-1 text-xs text-red-700"
            >
              {err}
            </li>
          ))}
        </ul>
      ) : null}
      <ActionHistory item={item} />
      <div className="mt-4 border-t border-slate-100 pt-4">
        <ReviewableCard item={item} onActionDone={onActionDone} failedOnly />
      </div>
    </article>
  );
}

function ReviewedCard({ item }: { item: HumanReviewQueueItem }) {
  const d = item.draftFinding;
  return (
    <article className="surface-card border-l-4 border-land-300 p-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="badge bg-land-50 text-land-700 ring-land-600/20">
          {item.latestStatus.replace(/_/g, " ")}
        </span>
        <RiskBadge level={riskFor(d.riskLevel)} />
        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
          {item.checklistItemId}
        </span>
      </div>
      <h3 className="mt-3 text-base font-semibold text-slate-900">{d.title}</h3>
      <p className="mt-2 text-sm text-slate-600">{d.summary}</p>
      <ActionHistory item={item} />
    </article>
  );
}
