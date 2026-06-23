export default function SafetyBoundaryBanner({
  variant = "default",
}: {
  variant?: "default" | "compact";
}) {
  if (variant === "compact") {
    return (
      <div className="flex items-start gap-3 rounded-lg border border-water-100 bg-water-50 px-4 py-3 text-sm text-slate-700">
        <span aria-hidden="true" className="mt-0.5 text-water-700">
          ⚖
        </span>
        <p>
          <span className="font-semibold text-slate-900">
            Review-support only.
          </span>{" "}
          Civil Engineer AI assists a human reviewer. It does not approve plans,
          certify compliance, stamp drawings, or replace a licensed Professional
          Engineer.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-water-100 bg-water-50 p-6">
      <div className="flex items-center gap-2">
        <span aria-hidden="true" className="text-water-700">
          ⚖
        </span>
        <h2 className="text-base font-semibold text-slate-900">
          Professional boundary
        </h2>
      </div>
      <p className="mt-3 text-sm text-slate-700">
        Civil Engineer AI assists review. It does not approve plans, certify
        compliance, stamp drawings, or replace a licensed Professional Engineer.
        Every finding is a review-support issue that needs reviewer confirmation
        and human judgment.
      </p>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-land-700">
            Sanctioned language
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Potential issue · Missing evidence · Conflicting information ·
            Requires reviewer confirmation · Recommended follow-up · Needs human
            review
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
            Never used
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Approved · Certified · Fully compliant · Safe · Engineer-confirmed ·
            Passes review · Meets all requirements
          </p>
        </div>
      </div>
    </div>
  );
}
