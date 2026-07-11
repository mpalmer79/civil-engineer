import type { CadFileReviewContext } from "@/lib/api";

// A compact review context summary for a CAD file: file metadata, latest parse
// run status, and finding count. This is extracted DXF review-support metadata,
// not a verification of the CAD file or the design.
export default function CadReviewContextPanel({
  context,
}: {
  context: CadFileReviewContext | null;
}) {
  if (!context) {
    return null;
  }
  const { cadFile, parseRun, summary } = context;
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Review context</h3>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <dt className="text-slate-600">File</dt>
        <dd className="text-slate-700">{cadFile.fileName}</dd>
        <dt className="text-slate-600">Upload status</dt>
        <dd className="text-slate-700">
          {cadFile.uploadStatus.replace(/_/g, " ")}
        </dd>
        <dt className="text-slate-600">Parse status</dt>
        <dd className="text-slate-700">
          {parseRun ? parseRun.status.replace(/_/g, " ") : "not parsed"}
        </dd>
        <dt className="text-slate-600">Findings</dt>
        <dd className="text-slate-700">{context.findings.length}</dd>
        <dt className="text-slate-600">Reference candidates</dt>
        <dd className="text-slate-700">
          {context.referenceCandidates.length}
        </dd>
        {summary ? (
          <>
            <dt className="text-slate-600">Layers</dt>
            <dd className="text-slate-700">{summary.layerCount}</dd>
          </>
        ) : null}
      </dl>
      <p className="mt-4 text-xs text-slate-600">{context.note}</p>
    </div>
  );
}
