"use client";

import type {
  CadMetadata,
  PlanReference,
  PlanSheetHotspot,
} from "@/lib/api";
import PlanStatusBadge from "@/components/PlanStatusBadge";

// Shows the civil feature references, CAD-aware metadata, documents, and
// checklist items connected to the selected hotspot. All of this is seeded
// review-support evidence, not extracted CAD.
export default function SheetReferencePanel({
  hotspot,
  cadMetadata,
  planReferences,
}: {
  hotspot: PlanSheetHotspot | null;
  cadMetadata: CadMetadata[];
  planReferences: PlanReference[];
}) {
  if (!hotspot) return null;

  const cad = cadMetadata.filter((c) =>
    hotspot.relatedCadMetadataIds.includes(c.cadMetadataId),
  );
  const references = planReferences.filter((r) =>
    hotspot.relatedPlanReferenceIds.includes(r.planReferenceId),
  );

  return (
    <div className="surface-card p-6">
      <h3 className="text-base font-semibold text-slate-900">
        Connected review evidence
      </h3>
      <p className="mt-1 text-xs text-slate-500">
        Seeded review-support metadata for the selected hotspot, not extracted
        CAD.
      </p>

      {references.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Plan references
          </p>
          <ul className="mt-2 space-y-2">
            {references.map((r) => (
              <li
                key={r.planReferenceId}
                className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{r.referenceLabel}</span>
                  <PlanStatusBadge status={r.consistencyStatus} />
                </div>
                {r.reviewNote ? (
                  <p className="mt-1 text-xs text-slate-500">{r.reviewNote}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {cad.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Civil feature metadata
          </p>
          <ul className="mt-2 space-y-2">
            {cad.map((c) => (
              <li
                key={c.cadMetadataId}
                className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{c.entityLabel}</span>
                  <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                    {c.entityType.replace(/_/g, " ")}
                  </span>
                  {c.layerName ? (
                    <span className="font-mono text-xs text-slate-400">
                      {c.layerName}
                    </span>
                  ) : null}
                </div>
                {c.notes ? (
                  <p className="mt-1 text-xs text-slate-500">{c.notes}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Documents
          </p>
          {hotspot.relatedDocumentIds.length > 0 ? (
            <ul className="mt-1 space-y-1 text-xs text-slate-600">
              {hotspot.relatedDocumentIds.map((d) => (
                <li key={d} className="font-mono">
                  {d}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-xs text-slate-400">None</p>
          )}
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Checklist items
          </p>
          {hotspot.relatedChecklistItemIds.length > 0 ? (
            <ul className="mt-1 space-y-1 text-xs text-slate-600">
              {hotspot.relatedChecklistItemIds.map((c) => (
                <li key={c} className="font-mono">
                  {c}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-xs text-slate-400">None</p>
          )}
        </div>
      </div>
    </div>
  );
}
