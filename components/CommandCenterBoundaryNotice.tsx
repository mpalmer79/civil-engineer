// A clear notice that the command center organizes review-support work and does
// not approve, certify, verify, validate, close, or resolve anything.
export default function CommandCenterBoundaryNotice({
  text,
}: {
  text?: string;
}) {
  const body =
    text ??
    "The Project Dashboard aggregates review-support data and links into the existing modules. It does not approve plans, certify compliance, verify CAD, validate design, declare a project safe, send official correspondence, or close or resolve issues. ready for human review means an area is organized enough for human review, never that it is complete or approved. All statuses are review-support statuses.";
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
      <p className="text-sm font-semibold text-amber-800">
        Command center limitations
      </p>
      <p className="mt-1 text-sm text-amber-700">{body}</p>
    </div>
  );
}
