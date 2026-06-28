"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";

import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import {
  getTraceabilityReviewActions,
  recordTraceabilityReviewAction,
  type ProjectTraceabilityLatestAction,
  type ProjectTraceabilityReviewAction,
  type ProjectTraceabilityRow,
  type ProjectTraceabilitySourceLink,
} from "@/lib/api";

// Review-support traceability matrix with client-side filters, inline review
// packet context, and reviewer review controls. Rows organize existing links and
// record how a reviewer reviewed each link. Nothing here states a requirement is
// satisfied, approved, certified, verified, or validated. Source links resolve to
// real project routes, or render "source link unavailable".

// Reviewer review action options. Labels stay review-support only: confirming a
// link confirms it is useful for review, not that a requirement is satisfied.
const REVIEW_ACTIONS: { value: string; label: string }[] = [
  { value: "reviewer_confirmed_link", label: "Confirm link for review" },
  { value: "needs_more_information", label: "Needs more information" },
  { value: "not_applicable", label: "Not applicable" },
  { value: "link_rejected", label: "Reject link" },
  { value: "follow_up_needed", label: "Follow-up needed" },
  { value: "needs_review", label: "Needs review" },
];

const ACTION_LABELS: Record<string, string> = Object.fromEntries(
  REVIEW_ACTIONS.map((a) => [a.value, a.label]),
);

function actionLabel(actionType: string): string {
  return ACTION_LABELS[actionType] ?? humanizeStatus(actionType);
}

function resolveRoute(
  projectId: string,
  link: ProjectTraceabilitySourceLink,
): { label: string; href: string } | null {
  const id = link.id ?? "";
  switch (link.type) {
    case "document":
      return id
        ? { label: "Document", href: `/projects/${projectId}/documents/${id}` }
        : null;
    case "finding":
      return id
        ? { label: "Finding", href: `/projects/${projectId}/findings/${id}` }
        : null;
    case "workflow_board":
      return {
        label: "Workflow board",
        href: `/projects/${projectId}/workflow-board`,
      };
    case "review_packet":
      return {
        label: "Review packets",
        href: `/projects/${projectId}/review-packets`,
      };
    case "plan_sheet":
      return id
        ? {
            label: "Plan sheet",
            href: `/projects/${projectId}/plan-sheets/${id}`,
          }
        : null;
    default:
      return null;
  }
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
      <span className="block">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={label}
        className="mt-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm font-normal normal-case text-slate-700"
      >
        <option value="all">All</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {humanizeStatus(opt)}
          </option>
        ))}
      </select>
    </label>
  );
}

function PacketContextCell({
  projectId,
  row,
}: {
  projectId: string;
  row: ProjectTraceabilityRow;
}) {
  const contexts = row.packetContexts ?? [];
  if (contexts.length === 0) {
    return (
      <span className="text-xs text-slate-400">
        not included in a packet yet
      </span>
    );
  }
  return (
    <div className="space-y-1.5 text-xs">
      {contexts.map((ctx) => (
        <div key={ctx.reviewPacketItemId}>
          <Link
            href={`/projects/${projectId}/review-packets`}
            className="font-medium text-water-700 hover:underline"
          >
            {ctx.reviewPacketTitle ?? "Review packet"}
          </Link>
          {ctx.packetItemStatus ? (
            <span className="block text-slate-500">
              {humanizeStatus(ctx.packetItemStatus)}
            </span>
          ) : null}
        </div>
      ))}
      {row.packetContextCount > contexts.length ? (
        <span className="block text-slate-400">
          and {row.packetContextCount - contexts.length} more
        </span>
      ) : null}
    </div>
  );
}

function RowReviewCell({
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
    setHistory(items);
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

export default function TraceabilityMatrix({
  projectId,
  rows,
}: {
  projectId: string;
  rows: ProjectTraceabilityRow[];
}) {
  const [status, setStatus] = useState("all");
  const [relationship, setRelationship] = useState("all");
  const [action, setAction] = useState("all");
  const [documentId, setDocumentId] = useState("all");
  const [source, setSource] = useState("all");
  const [packet, setPacket] = useState("all");

  const unique = useCallback(
    (selector: (r: ProjectTraceabilityRow) => string | null) =>
      Array.from(
        new Set(rows.map(selector).filter((v): v is string => Boolean(v))),
      ).sort(),
    [rows],
  );

  const filtered = useMemo(
    () =>
      rows.filter((r) => {
        if (status !== "all" && r.checklistStatus !== status) return false;
        if (relationship !== "all" && r.relationshipType !== relationship)
          return false;
        if (action === "yes" && !r.reviewerActionNeeded) return false;
        if (action === "no" && r.reviewerActionNeeded) return false;
        if (documentId !== "all" && r.documentId !== documentId) return false;
        if (source !== "all" && r.relationshipSource !== source) return false;
        if (packet === "in" && (r.packetContextCount ?? 0) === 0) return false;
        if (packet === "out" && (r.packetContextCount ?? 0) > 0) return false;
        return true;
      }),
    [rows, status, relationship, action, documentId, source, packet],
  );

  const activeCount = [
    status,
    relationship,
    action,
    documentId,
    source,
    packet,
  ].filter((v) => v !== "all").length;

  const reset = () => {
    setStatus("all");
    setRelationship("all");
    setAction("all");
    setDocumentId("all");
    setSource("all");
    setPacket("all");
  };

  return (
    <div className="space-y-4">
      <div className="surface-card p-4">
        <div className="flex flex-wrap items-end gap-3">
          <FilterSelect
            label="Checklist status"
            value={status}
            onChange={setStatus}
            options={unique((r) => r.checklistStatus)}
          />
          <FilterSelect
            label="Relationship type"
            value={relationship}
            onChange={setRelationship}
            options={unique((r) => r.relationshipType)}
          />
          <FilterSelect
            label="Reviewer action needed"
            value={action}
            onChange={setAction}
            options={["yes", "no"]}
          />
          <FilterSelect
            label="Document"
            value={documentId}
            onChange={setDocumentId}
            options={unique((r) => r.documentId)}
          />
          <FilterSelect
            label="Source type"
            value={source}
            onChange={setSource}
            options={unique((r) => r.relationshipSource)}
          />
          <FilterSelect
            label="Packet inclusion"
            value={packet}
            onChange={setPacket}
            options={["in", "out"]}
          />
          <button
            type="button"
            onClick={reset}
            disabled={activeCount === 0}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Reset filters
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          {activeCount === 0
            ? "No filters applied. Showing all linked review-support rows."
            : `${activeCount} filter(s) applied. Showing ${filtered.length} of ${rows.length} rows.`}
        </p>
      </div>

      {filtered.length === 0 ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          No rows match the current filters. This is a filtered view, not a
          statement that requirements are satisfied or unsupported.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Requirement</th>
                <th className="py-2 pr-4">Linked evidence</th>
                <th className="py-2 pr-4">Finding / workflow</th>
                <th className="py-2 pr-4">Packet context</th>
                <th className="py-2 pr-4">Relationship</th>
                <th className="py-2 pr-4">Source links</th>
                <th className="py-2 pr-4">Reviewer review</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr
                  key={r.traceabilityRowId}
                  className="border-b border-slate-100 align-top"
                >
                  <td className="py-2 pr-4">
                    <span className="font-medium text-slate-800">
                      {r.checklistTitle ?? r.checklistItemId}
                    </span>
                    {r.checklistRequirement ? (
                      <span className="block max-w-xs text-xs text-slate-500">
                        {r.checklistRequirement}
                      </span>
                    ) : null}
                    {r.checklistStatus ? (
                      <span className="mt-1 block text-xs text-slate-400">
                        {humanizeStatus(r.checklistStatus)}
                      </span>
                    ) : null}
                  </td>
                  <td className="py-2 pr-4 text-slate-700">
                    {r.relationshipType === "no_linked_evidence_yet" ? (
                      <span className="text-slate-400">
                        {r.notes === "not_enough_indexed_information"
                          ? "not enough indexed information"
                          : "no linked evidence yet"}
                      </span>
                    ) : (
                      <>
                        {r.documentName ?? r.documentId ?? "linked evidence"}
                        {r.pageNumber ? (
                          <span className="block text-xs text-slate-500">
                            page {r.pageNumber}
                          </span>
                        ) : null}
                        {r.citationExcerpt ? (
                          <span className="block max-w-xs text-xs italic text-slate-500">
                            &ldquo;{r.citationExcerpt}&rdquo;
                          </span>
                        ) : null}
                      </>
                    )}
                  </td>
                  <td className="py-2 pr-4 text-xs text-slate-600">
                    {r.findingTitle ? <span>{r.findingTitle}</span> : null}
                    {r.workflowItemTitle ? (
                      <span className="block text-slate-500">
                        {r.workflowItemTitle}
                      </span>
                    ) : null}
                    {!r.findingTitle && !r.workflowItemTitle ? (
                      <span className="text-slate-400">none</span>
                    ) : null}
                  </td>
                  <td className="py-2 pr-4">
                    <PacketContextCell projectId={projectId} row={r} />
                  </td>
                  <td className="py-2 pr-4">
                    <StatusChip label={humanizeStatus(r.relationshipType)} />
                  </td>
                  <td className="py-2 pr-4 text-xs">
                    <div className="flex flex-wrap gap-1.5">
                      {r.sourceLinks.length === 0 ? (
                        <span className="text-slate-400">none</span>
                      ) : (
                        r.sourceLinks.map((link, i) => {
                          const route = resolveRoute(projectId, link);
                          return route ? (
                            <Link
                              key={`${link.type}:${i}`}
                              href={route.href}
                              className="rounded-md bg-water-50 px-2 py-1 font-medium text-water-700 hover:bg-water-100"
                            >
                              {route.label}
                            </Link>
                          ) : (
                            <span
                              key={`${link.type}:${i}`}
                              className="rounded-md bg-slate-100 px-2 py-1 text-slate-500"
                            >
                              source link unavailable
                            </span>
                          );
                        })
                      )}
                    </div>
                  </td>
                  <td className="py-2 pr-4">
                    <RowReviewCell projectId={projectId} row={r} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
