// Controls for promoting selected CAD findings into the workflow board. A
// reviewer records their name and an optional note, then promotes the selected
// findings. Promotion creates review-support workflow items under human review.
// It does not approve, certify, verify, or validate anything. The backend
// prevents duplicate workflow items from the same CAD finding.
export default function CadFindingPromotionPanel({
  reviewerName,
  reviewerNote,
  onReviewerNameChange,
  onReviewerNoteChange,
  selectedCount,
  busy,
  onPromoteSelected,
  resultMessage,
}: {
  reviewerName: string;
  reviewerNote: string;
  onReviewerNameChange: (value: string) => void;
  onReviewerNoteChange: (value: string) => void;
  selectedCount: number;
  busy: boolean;
  onPromoteSelected: () => void;
  resultMessage: string | null;
}) {
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Promote findings to workflow
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        Promote {selectedCount} selected CAD finding(s) into the workflow board.
        Already promoted findings are skipped so no duplicate workflow items are
        created.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <label
            htmlFor="cad-promotion-reviewer-name"
            className="block text-xs font-semibold uppercase tracking-wide text-slate-500"
          >
            Reviewer name
          </label>
          <input
            id="cad-promotion-reviewer-name"
            type="text"
            value={reviewerName}
            onChange={(e) => onReviewerNameChange(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label
            htmlFor="cad-promotion-reviewer-note"
            className="block text-xs font-semibold uppercase tracking-wide text-slate-500"
          >
            Reviewer note (optional)
          </label>
          <input
            id="cad-promotion-reviewer-note"
            type="text"
            value={reviewerNote}
            onChange={(e) => onReviewerNoteChange(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
      </div>
      <button
        type="button"
        onClick={onPromoteSelected}
        disabled={busy || selectedCount === 0}
        className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy
          ? "Promoting..."
          : `Promote ${selectedCount} selected finding(s)`}
      </button>
      {resultMessage ? (
        <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {resultMessage}
        </p>
      ) : null}
    </div>
  );
}
