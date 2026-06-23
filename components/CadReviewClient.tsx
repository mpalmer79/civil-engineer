"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getCadMetadata,
  getPlanReferences,
  getPlanConsistencyFindings,
  runPlanConsistencyCheck,
  type CadMetadata,
  type PlanReference,
  type PlanConsistencyFinding,
} from "@/lib/api";
import RiskBadge from "@/components/RiskBadge";

const riskFor = (level: string) =>
  level === "high" || level === "medium" || level === "low"
    ? (level as "high" | "medium" | "low")
    : "low";

const CONSISTENCY_STYLES: Record<string, string> = {
  consistent: "bg-land-50 text-land-700 ring-land-600/20",
  missing_target: "bg-red-50 text-red-700 ring-red-600/20",
  conflicting_label: "bg-red-50 text-red-700 ring-red-600/20",
  unclear: "bg-yellow-50 text-yellow-700 ring-yellow-600/20",
  needs_human_review: "bg-yellow-50 text-yellow-700 ring-yellow-600/20",
};

const FINDING_LABELS: Record<string, string> = {
  missing_referenced_sheet: "Missing referenced sheet",
  missing_sheet: "Missing sheet",
  conflicting_label: "Conflicting label",
  missing_plan_reference: "Missing plan reference",
  unclear_revision: "Unclear revision",
  cad_metadata_gap: "CAD metadata gap",
  requires_human_review: "Requires human review",
};

export default function CadReviewClient() {
  const [metadata, setMetadata] = useState<CadMetadata[]>([]);
  const [references, setReferences] = useState<PlanReference[]>([]);
  const [findings, setFindings] = useState<PlanConsistencyFinding[]>([]);
  const [entityFilter, setEntityFilter] = useState<string>("all");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [backendUp, setBackendUp] = useState(true);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    const [meta, refs, finds] = await Promise.all([
      getCadMetadata(),
      getPlanReferences(),
      getPlanConsistencyFindings(),
    ]);
    setMetadata(meta);
    setReferences(refs);
    setFindings(finds);
    setBackendUp(meta.length > 0 || refs.length > 0);
    setLoaded(true);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const entityTypes = useMemo(
    () => Array.from(new Set(metadata.map((m) => m.entityType))).sort(),
    [metadata],
  );

  const filteredMetadata = useMemo(
    () =>
      entityFilter === "all"
        ? metadata
        : metadata.filter((m) => m.entityType === entityFilter),
    [metadata, entityFilter],
  );

  const handleCheck = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await runPlanConsistencyCheck();
    if (result.ok && result.findings) {
      setFindings(result.findings);
      setMessage(
        `Plan consistency check completed: ${result.findings.length} review-support findings. All require human review.`,
      );
      await refresh();
    } else {
      setMessage(result.error ?? "Plan consistency check failed.");
      if (!result.backendReachable) setBackendUp(false);
    }
    setBusy(false);
  }, [refresh]);

  if (loaded && !backendUp) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-base font-semibold text-slate-900">
          CAD-aware review
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          Phase 6 uses seeded CAD-aware metadata, not live CAD parsing.
        </p>
        <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
          The backend is not reachable. CAD-aware metadata and plan consistency
          checks require the API. Consistency findings are never simulated in
          the browser.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Plan consistency review
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              Run the plan consistency check to compare seeded plan sheets,
              references, and CAD-aware metadata. The check surfaces missing
              sheets, conflicting labels, and references that need human review.
              It does not validate a design or verify a CAD drawing.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCheck}
            disabled={busy}
            className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Running check..." : "Run plan consistency check"}
          </button>
        </div>
        {message ? (
          <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
            {message}
          </p>
        ) : null}
      </div>

      {/* Plan consistency findings */}
      <section className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-900">
          Plan consistency findings ({findings.length})
        </h3>
        {findings.length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {findings.map((f) => (
              <article key={f.planFindingId} className="surface-card p-6">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge bg-water-50 text-water-700 ring-water-600/20">
                    {FINDING_LABELS[f.findingType] ?? f.findingType}
                  </span>
                  <RiskBadge level={riskFor(f.riskLevel)} />
                  <span className="badge bg-yellow-50 text-yellow-700 ring-yellow-600/20">
                    Needs human review
                  </span>
                </div>
                <h4 className="mt-3 text-base font-semibold text-slate-900">
                  {f.title}
                </h4>
                <p className="mt-2 text-sm text-slate-600">{f.summary}</p>
                <div className="mt-3 text-sm">
                  <p className="font-semibold text-slate-700">
                    Recommended human action
                  </p>
                  <p className="mt-0.5 text-slate-600">
                    {f.recommendedHumanAction}
                  </p>
                </div>
                <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3 text-xs text-slate-500">
                  {f.relatedSheetIds.length > 0 ? (
                    <span className="rounded bg-slate-50 px-2 py-1">
                      sheets: {f.relatedSheetIds.length}
                    </span>
                  ) : null}
                  {f.relatedCadMetadataIds.length > 0 ? (
                    <span className="rounded bg-slate-50 px-2 py-1">
                      civil features: {f.relatedCadMetadataIds.length}
                    </span>
                  ) : null}
                  {f.relatedChecklistItems.length > 0 ? (
                    <span className="rounded bg-slate-50 px-2 py-1">
                      checklist: {f.relatedChecklistItems.join(", ")}
                    </span>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
            No plan consistency findings yet. Run the plan consistency check to
            generate review-support findings.
          </p>
        )}
      </section>

      {/* Civil feature metadata */}
      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-lg font-semibold text-slate-900">
            CAD-aware civil feature metadata ({filteredMetadata.length})
          </h3>
          <label className="text-sm">
            <span className="mr-2 font-medium text-slate-700">
              Entity type
            </span>
            <select
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
            >
              <option value="all">all</option>
              {entityTypes.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="surface-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Feature</th>
                  <th className="px-4 py-3">Entity type</th>
                  <th className="px-4 py-3">Layer</th>
                  <th className="px-4 py-3">Sheet</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredMetadata.map((m) => (
                  <tr key={m.cadMetadataId} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">
                      {m.entityLabel}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {m.entityType.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">
                      {m.layerName ?? "-"}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">
                      {m.sheetId ?? "-"}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {m.sourceType.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {m.notes ?? ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Plan references */}
      <section className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-900">
          Civil feature references ({references.length})
        </h3>
        <div className="surface-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Reference</th>
                  <th className="px-4 py-3">Consistency status</th>
                  <th className="px-4 py-3">Review note</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {references.map((r) => (
                  <tr key={r.planReferenceId} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-slate-700">
                      {r.referenceLabel}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`badge ${
                          CONSISTENCY_STYLES[r.consistencyStatus] ??
                          "bg-slate-100 text-slate-600 ring-slate-300"
                        }`}
                      >
                        {r.consistencyStatus.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {r.reviewNote ?? ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Future integration panel */}
      <section className="surface-card p-6">
        <h3 className="text-base font-semibold text-slate-900">
          Future CAD and Autodesk integration path
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          Phase 6 establishes a CAD-aware metadata foundation. No CAD file is
          parsed and no Autodesk integration exists yet. The roadmap below is
          planned, not implemented.
        </p>
        <ol className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
          <li className="rounded-lg bg-slate-50 px-3 py-2">
            Phase 6: Seeded plan sheet and CAD-aware metadata
          </li>
          <li className="rounded-lg bg-slate-50 px-3 py-2">
            Phase 7: Plan sheet PDF viewer and sheet hotspot annotations
          </li>
          <li className="rounded-lg bg-slate-50 px-3 py-2">
            Phase 8: DXF metadata extraction or structured plan exports
          </li>
          <li className="rounded-lg bg-slate-50 px-3 py-2">
            Phase 9: Autodesk Platform Services viewer exploration
          </li>
          <li className="rounded-lg bg-slate-50 px-3 py-2">
            Phase 10: CAD and document cross-reference automation
          </li>
        </ol>
      </section>
    </div>
  );
}
