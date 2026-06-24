"use client";

import { useEffect, useState } from "react";
import {
  getReviewPacketTraceability,
  type ReviewPacketTraceability,
} from "@/lib/api";

// Loads and renders the evidence traceability matrix for a packet. Each row
// traces a packet item to one source evidence entity.
export default function EvidenceTraceabilityMatrix({
  packetId,
}: {
  packetId: string;
}) {
  const [data, setData] = useState<ReviewPacketTraceability | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      setData(await getReviewPacketTraceability(packetId));
      setLoaded(true);
    })();
  }, [packetId]);

  if (loaded && !data) {
    return (
      <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
        The backend is required to load the traceability matrix.
      </p>
    );
  }
  if (!data) {
    return (
      <p className="surface-card p-4 text-sm text-slate-500">
        Loading traceability matrix...
      </p>
    );
  }

  return (
    <div className="surface-card overflow-hidden">
      <div className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-base font-semibold text-slate-900">
          Evidence traceability matrix ({data.totalRows} rows)
        </h3>
        <p className="mt-1 text-xs text-slate-500">{data.note}</p>
      </div>
      <div className="max-h-[28rem] overflow-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="sticky top-0 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Section</th>
              <th className="px-4 py-3">Item</th>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Evidence</th>
              <th className="px-4 py-3">Relationship</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.rows.map((r, i) => (
              <tr key={`${r.itemId}-${i}`} className="hover:bg-slate-50">
                <td className="px-4 py-2 text-xs text-slate-500">
                  {r.sectionType.replace(/_/g, " ")}
                </td>
                <td className="px-4 py-2 text-slate-700">
                  <div>{r.itemTitle}</div>
                  <div className="font-mono text-xs text-slate-400">
                    {r.sourceType}
                    {r.sourceId ? ` / ${r.sourceId}` : ""}
                  </div>
                </td>
                <td className="px-4 py-2 font-mono text-xs text-slate-500">
                  {r.sourceType}
                </td>
                <td className="px-4 py-2 font-mono text-xs text-slate-500">
                  {r.evidenceType} / {r.evidenceId}
                </td>
                <td className="px-4 py-2 text-xs text-slate-600">
                  {r.relationship.replace(/_/g, " ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
