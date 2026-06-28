// Renders a backend-provided professional boundary or limitations note. Use this
// to surface fields such as limitations_note, note, or draft_notice. These notes
// keep the review-support boundary visible; they are never stripped to make a
// page look cleaner. Renders nothing when no note text is provided.
export default function BoundaryNote({
  note,
  title = "Review-support boundary",
}: {
  note?: string | null;
  title?: string;
}) {
  const text = (note ?? "").trim();
  if (!text) return null;
  return (
    <div className="flex items-start gap-3 rounded-lg border border-water-100 bg-water-50 px-4 py-3 text-sm text-slate-700">
      <span aria-hidden="true" className="mt-0.5 text-water-700">
        ⚖
      </span>
      <p>
        <span className="font-semibold text-slate-900">{title}.</span> {text}
      </p>
    </div>
  );
}
