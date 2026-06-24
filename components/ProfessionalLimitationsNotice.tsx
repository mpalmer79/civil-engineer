// A clear notice that the review packet is draft review-support material and
// does not approve, certify, stamp, verify CAD, or validate the design.
export default function ProfessionalLimitationsNotice({
  text,
}: {
  text?: string;
}) {
  const body =
    text ??
    "This packet is draft review-support material. It organizes evidence for a human reviewer and does not approve plans, certify compliance, stamp drawings, verify CAD, validate the design, or replace a licensed Professional Engineer.";
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
      <p className="text-sm font-semibold text-amber-800">
        Professional limitations and review boundary
      </p>
      <p className="mt-1 text-sm text-amber-700">{body}</p>
    </div>
  );
}
