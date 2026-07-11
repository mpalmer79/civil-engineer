import type { CadParseRun, CadParseSummary } from "@/lib/api";

function CountChips({ counts }: { counts: Record<string, number> }) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) {
    return <p className="mt-1 text-sm text-slate-600">None</p>;
  }
  return (
    <div className="mt-1 flex flex-wrap gap-2">
      {entries.map(([key, value]) => (
        <span
          key={key}
          className="rounded-md bg-slate-50 px-2.5 py-1 text-xs text-slate-700"
        >
          {key.replace(/_/g, " ")}: <strong>{value}</strong>
        </span>
      ))}
    </div>
  );
}

// Header card for a DXF parse run: status and extraction counts.
export default function CadParseSummaryCard({
  run,
  summary,
}: {
  run: CadParseRun | null;
  summary: CadParseSummary | null;
}) {
  if (!run) {
    return null;
  }
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">Parse run</h3>
        <span className="text-sm text-slate-600">
          {run.parserName} {run.parserVersion} · status:{" "}
          {run.status.replace(/_/g, " ")}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-5">
        {[
          ["Entities", run.entityCount],
          ["Layers", run.layerCount],
          ["Blocks", run.blockCount],
          ["Text", run.textCount],
          ["Warnings", run.warningCount],
        ].map(([label, value]) => (
          <div key={label} className="rounded-lg bg-slate-50 px-3 py-2">
            <p className="text-xs uppercase tracking-wide text-slate-600">
              {label}
            </p>
            <p className="text-lg font-semibold text-slate-900">{value}</p>
          </div>
        ))}
      </div>
      {run.errorMessage ? (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {run.errorMessage}
        </p>
      ) : null}
      {summary ? (
        <div className="mt-4 space-y-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
              Layers by category
            </p>
            <CountChips counts={summary.layersByCategory} />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
              References by confidence
            </p>
            <CountChips counts={summary.referencesByConfidence} />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
              Findings by type
            </p>
            <CountChips counts={summary.findingsByType} />
          </div>
        </div>
      ) : null}
      <p className="mt-4 text-xs text-slate-600">{run.limitationsNote}</p>
    </div>
  );
}
