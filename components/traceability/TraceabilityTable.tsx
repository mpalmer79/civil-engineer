import Link from "next/link";

import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import RowReviewCell from "@/components/traceability/RowReviewCell";
import { resolveRoute } from "@/components/traceability/traceabilityHelpers";
import type { ProjectTraceabilityRow } from "@/lib/api";

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

// The filtered traceability rows. Source links resolve to real project routes,
// or render "source link unavailable".
export default function TraceabilityTable({
  projectId,
  rows,
}: {
  projectId: string;
  rows: ProjectTraceabilityRow[];
}) {
  return (
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
          {rows.map((r) => (
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
  );
}
