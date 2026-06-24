// A clear notice that CAD intake is DXF metadata extraction for review support
// only. It does not verify CAD, validate geometry or design, certify
// compliance, approve plans, or replace a licensed Professional Engineer.
export default function CadLimitationsNotice({ text }: { text?: string }) {
  const body =
    text ??
    "This is DXF metadata extraction for review support only. Civil Engineer AI does not verify CAD, validate geometry, hydraulic calculations, grading, stormwater design, or legal boundaries, certify compliance, approve plans, or replace a licensed Professional Engineer. DXF is the only supported file type in this phase; DWG parsing is future work.";
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
      <p className="text-sm font-semibold text-amber-800">
        CAD intake limitations
      </p>
      <p className="mt-1 text-sm text-amber-700">{body}</p>
    </div>
  );
}
