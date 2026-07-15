"use client";

import { useCallback, useState } from "react";

import {
  actionLabel,
  REVIEW_ACTIONS,
} from "@/components/traceability/traceabilityHelpers";
import {
  getTraceabilityReviewActions,
  recordTraceabilityReviewAction,
  type ProjectTraceabilityLatestAction,
  type ProjectTraceabilityReviewAction,
  type ProjectTraceabilityRow,
} from "@/lib/api";

// Inline reviewer review controls for a single traceability row. Records how a
// reviewer reviewed a link; it never states a requirement is satisfied.
export default function RowReviewCell({
  projectId,
  row,
}: {
  projectId: string;
  row: ProjectTraceabilityRow;
}) {
  const [latest, setLatest] = useState<ProjectTraceabilityLatestAction | null>(
    row.latestReviewAction,
  );
  const [actionType, setActionType] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<
    ProjectTraceabilityReviewAction[] | null
  >(null);
  const [showHistory, setShowHistory] = useState(false);

  const loadHistory = useCallback(async () => {
    const items = await getTraceabilityReviewActions(
      projectId,
      row.traceabilityRowKey,
    );
    setHistory(items.ok ? items.data : null);
  }, [projectId, row.traceabilityRowKey]);

  async function submit() {
    if (!actionType) return;
    setBusy(true);
    setError(null);
    const result = await recordTraceabilityReviewAction(
      projectId,
      row.traceabilityRowKey,
      {
        actionType,
        reviewerNote: note.trim() || undefined,
        checklistItemId: row.checklistItemId,
        evidenceCitationId: row.evidenceCitationId,
        evidenceCandidateId: row.evidenceCandidateId,
        findingId: row.findingId,
        workflowItemId: row.workflowItemId,
        reviewPacketItemId: row.reviewPacketItemId,
        relationshipType: row.relationshipType,
      },
    );
    setBusy(false);
    if (!result.ok || !result.action) {
      setError(result.error ?? "Could not record the review action.");
      return;
    }
    setLatest({
      actionId: result.action.actionId,
      actionType: result.action.actionType,
      reviewerNote: result.action.reviewerNote,
      createdBy: result.action.createdBy,
      createdAt: result.action.createdAt,
    });
    setActionType("");
    setNote("");
    if (showHistory) await loadHistory();
  }

  async function toggleHistory() {
    const next = !showHistory;
    setShowHistory(next);
    if (next && history === null) await loadHistory();
  }

  return (
    <div className="space-y-2 text-xs">
      <div>
        {latest ? (
          <span className="text-slate-700">
            Latest:{" "}
            <span className="font-medium">{actionLabel(latest.actionType)}</span>
            {latest.createdBy ? (
              <span className="text-slate-500"> by {latest.createdBy}</span>
            ) : null}
            {latest.reviewerNote ? (
              <span className="block italic text-slate-500">
                &ldquo;{latest.reviewerNote}&rdquo;
              </span>
            ) : null}
          </span>
        ) : (
          <span className="text-amber-700">requires reviewer confirmation</span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <select
          value={actionType}
          onChange={(e) => setActionType(e.target.value)}
          aria-label={`Review action for ${
            row.checklistTitle ?? row.traceabilityRowKey
          }`}
          className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700"
        >
          <option value="">Record review action...</option>
          {REVIEW_ACTIONS.map((a) => (
            <option key={a.value} value={a.value}>
              {a.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={submit}
          disabled={!actionType || busy}
          className="rounded-md bg-water-600 px-2 py-1 text-xs font-semibold text-white hover:bg-water-700 disabled:opacity-50"
        >
          {busy ? "Saving..." : "Save"}
        </button>
        <button
          type="button"
          onClick={toggleHistory}
          className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50"
        >
          {showHistory ? "Hide history" : "View history"}
        </button>
      </div>

      <input
        type="text"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Optional reviewer note"
        aria-label={`Reviewer note for ${
          row.checklistTitle ?? row.traceabilityRowKey
        }`}
        className="w-full rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700"
      />

      {error ? <p className="text-rose-600">{error}</p> : null}

      {showHistory ? (
        history && history.length > 0 ? (
          <ul className="space-y-1 border-l border-slate-200 pl-2">
            {history.map((h) => (
              <li key={h.actionId} className="text-slate-600">
                <span className="font-medium">{actionLabel(h.actionType)}</span>
                {h.createdBy ? (
                  <span className="text-slate-500"> by {h.createdBy}</span>
                ) : null}
                {h.reviewerNote ? (
                  <span className="block italic text-slate-500">
                    &ldquo;{h.reviewerNote}&rdquo;
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-slate-400">
            No reviewer review actions recorded yet.
          </p>
        )
      ) : null}
    </div>
  );
}
