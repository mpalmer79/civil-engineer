"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getCadMetadata,
  getPlanConsistencyFindings,
  getPlanConsistencySummary,
  getPlanReferences,
  runPlanConsistencyCheck,
  type CadMetadata,
  type PlanConsistencyFinding,
  type PlanConsistencySummary,
  type PlanReference,
} from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import PlanStatusBadge from "@/components/PlanStatusBadge";

export default function CadReviewClient() {
  const [metadata, setMetadata] = useState<CadMetadata[]>([]);
  const [references, setReferences] = useState<PlanReference[]>([]);
  const [findings, setFindings] = useState<PlanConsistencyFinding[]>([]);
  const [summary, setSummary] = useState<PlanConsistencySummary | null>(null);
  const [entityType, setEntityType] = useState<string>("all");
  const [backendUp, setBackendUp] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [meta, refs, finds, sum] = await Promise.all([
      getCadMetadata(),
      getPlanReferences(),
      getPlanConsistencyFindings(),
      getPlanConsistencySummary(),
    ]);
    if (meta.length === 0 && refs.length === 0) {
      setBackendUp(false);
      return;
    }
    setBackendUp(true);
    setMetadata(meta);
    setReferences(refs);
    setFindings(finds);
    setSummary(sum);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const entityTypes = useMemo(() => {
    const types = new Set(metadata.map((m) => m.entityType));
    return ["all", ...Array.from(types).sort()];
  }, [metadata]);

  const filteredMetadata = useMemo(
    () =>
      entityType === "all"
        ? metadata
        : metadata.filter((m) => m.entityType === entityType),
    [metadata, entityType],
  );

  const handleRunCheck = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await runPlanConsistencyCheck();
    if (result.ok && result.summary) {
      setSummary(result.summary);
      setFindings(await getPlanConsistencyFindings());
      setMessage(
        `Plan consistency check completed: ${result.summary.planConsistencyFindings} findings require human review.`,
      );
    } else {
      setMessage(result.error ?? "The plan consistency check failed.");
      if (!result.backendReachable) setBackendUp(false);
    }
    setBusy(false);
  }, []);

  if (!backendUp) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-base font-semibold text-slate-900">
          CAD-aware review
        </h3>
        <p className="mt-2 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
          The backend is required for CAD-aware metadata and the plan
          consistency check. Start the API to load the seeded Brookside Meadows
          plan data. Plan consistency findings are not simulated in the browser.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {summary ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <MetricCard
            value={summary.cadMetadataRecords}
            label="CAD-aware metadata records"
            accent="water"
          />
          <MetricCard
            value={summary.totalPlanReferences}
            label="Plan references"
            accent="water"
          />
          <MetricCard
            value={summary.inconsistentReferences}
            label="Inconsistent references"
            accent="amber"
          />
          <MetricCard
            value={summary.missingSheetCount}
            label="Missing sheets"
            accent="red"
          />
          <MetricCard
            value={summary.findingsRequiringHumanReview}
            label="Findings needing human review"
            accent="amber"
          />
        </div>
      ) : null}

      <div className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Plan consistency review
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-slate-600">
              Run the plan consistency check to re-evaluate the seeded plan
              references and sheets. The check surfaces missing targets,
              conflicting labels, and unclear revisions as review-support
              findings that need reviewer confirmation. It does not verify CAD
              drawings or validate the design.
            </p>
          </div>
          <button
            type="button"
            onClick={handleRunCheck}
            disabled={busy}
            className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Running..." : "Run plan consistency check"}
          </button>
        </div>
        {message ? (
          <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
            {message}
          </p>
        ) : null}
      </div>

      <div className="surface-card overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Civil feature metadata
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Seeded or derived CAD-aware review metadata. Real DXF extraction
              happens in CAD Intake.
            </p>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            Entity type
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
            >
              {entityTypes.map((t) => (
                <option key={t} value={t}>
                  {t === "all" ? "All entity types" : t.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Feature</th>
                <th className="px-4 py-3">Entity type</th>
                <th className="px-4 py-3">Discipline</th>
                <th className="px-4 py-3">Sheet</th>
                <th className="px-4 py-3">Layer</th>
                <th className="px-4 py-3">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredMetadata.map((m) => (
                <tr key={m.cadMetadataId} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-700">
                    {m.entityLabel}
                    {m.notes ? (
                      <div className="mt-0.5 text-xs text-slate-500">
                        {m.notes}
                      </div>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {m.entityType.replace(/_/g, " ")}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {m.discipline.replace(/_/g, " ")}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">
                    {m.sheetId ?? "-"}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">
                    {m.layerName ?? "-"}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {m.sourceType.replace(/_/g, " ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="surface-card overflow-hidden">
        <div className="border-b border-slate-100 px-4 py-3">
          <h3 className="text-base font-semibold text-slate-900">
            Civil feature references
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Where the package points from a document, sheet, or feature to
            another, and whether the target was located and labels agree.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Reference</th>
                <th className="px-4 py-3">Context</th>
                <th className="px-4 py-3">Consistency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {references.map((r) => (
                <tr key={r.planReferenceId} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-700">
                    {r.referenceLabel}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {r.referenceContext}
                  </td>
                  <td className="px-4 py-3">
                    <PlanStatusBadge status={r.consistencyStatus} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="surface-card overflow-hidden">
        <div className="border-b border-slate-100 px-4 py-3">
          <h3 className="text-base font-semibold text-slate-900">
            Plan consistency findings
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Review-support findings generated from the plan references and
            sheets. Each one requires human review.
          </p>
        </div>
        {findings.length === 0 ? (
          <p className="px-4 py-4 text-sm text-slate-500">
            No plan consistency findings yet. Run the plan consistency check to
            generate them.
          </p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {findings.map((f) => (
              <li key={f.planFindingId} className="px-4 py-4">
                <div className="flex flex-wrap items-center gap-2">
                  <PlanStatusBadge status={f.findingType} />
                  <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                    risk: {f.riskLevel}
                  </span>
                  <PlanStatusBadge status={f.status} />
                </div>
                <h4 className="mt-2 text-sm font-semibold text-slate-900">
                  {f.title}
                </h4>
                <p className="mt-1 text-sm text-slate-600">{f.summary}</p>
                <p className="mt-2 text-xs text-slate-500">
                  <span className="font-semibold text-slate-700">
                    Recommended human action:
                  </span>{" "}
                  {f.recommendedHumanAction}
                </p>
                {f.relatedSheetIds.length ||
                f.relatedCadMetadataIds.length ||
                f.relatedChecklistItems.length ? (
                  <p className="mt-2 text-xs text-slate-400">
                    sheets: {f.relatedSheetIds.join(", ") || "-"} · features:{" "}
                    {f.relatedCadMetadataIds.join(", ") || "-"} · checklist:{" "}
                    {f.relatedChecklistItems.join(", ") || "-"}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
