// A clear notice that multi-round review tracking and revision comparison are
// review-support only. Revision comparison uses extracted DXF metadata and does
// not verify CAD geometry, validate design, approve plans, certify compliance,
// or replace a licensed Professional Engineer. All statuses are review-support
// statuses, not final engineering decisions.
export default function MultiRoundReviewBoundaryNotice({
  text,
}: {
  text?: string;
}) {
  const body =
    text ??
    "Review cycles, resubmittal intake, and revision comparison organize review-support evidence across review rounds. Revision comparison uses extracted DXF metadata only (layers, references, blocks, and review findings). It does not verify CAD geometry, validate design, approve plans, certify compliance, send official correspondence, or replace a licensed Professional Engineer. All statuses are review-support statuses, not final engineering decisions.";
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
      <p className="text-sm font-semibold text-amber-800">
        Multi-round review limitations
      </p>
      <p className="mt-1 text-sm text-amber-700">{body}</p>
    </div>
  );
}
