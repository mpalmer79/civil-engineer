// Shown when no CAD file is loaded yet. Offers the bundled sample DXF as a
// starting point.
export default function CadIntakeEmptyState({
  busy,
  message,
  onLoadSample,
}: {
  busy: boolean;
  message: string | null;
  onLoadSample: () => Promise<void>;
}) {
  return (
    <div className="surface-card p-6">
      <p className="text-sm text-slate-600">
        No CAD file is loaded yet. Upload a DXF file above, or register and
        parse the bundled Brookside Meadows sample DXF.
      </p>
      <button
        type="button"
        onClick={onLoadSample}
        disabled={busy}
        className="mt-4 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50 disabled:opacity-60"
      >
        {busy ? "Working..." : "Load and parse sample DXF"}
      </button>
      {message ? (
        <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {message}
        </p>
      ) : null}
    </div>
  );
}
