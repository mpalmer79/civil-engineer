"use client";

import { useCallback, useMemo, useState } from "react";

import FilterSelect from "@/components/traceability/FilterSelect";
import TraceabilityTable from "@/components/traceability/TraceabilityTable";
import { filterTraceabilityRows } from "@/components/traceability/traceabilityHelpers";
import type { ProjectTraceabilityRow } from "@/lib/api";

// Review-support traceability matrix with client-side filters, inline review
// packet context, and reviewer review controls. Rows organize existing links and
// record how a reviewer reviewed each link. Nothing here states a requirement is
// satisfied, approved, certified, verified, or validated. Source links resolve to
// real project routes, or render "source link unavailable".
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
      filterTraceabilityRows(rows, {
        status,
        relationship,
        action,
        documentId,
        source,
        packet,
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
        <TraceabilityTable projectId={projectId} rows={filtered} />
      )}
    </div>
  );
}
