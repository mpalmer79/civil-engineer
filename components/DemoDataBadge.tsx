// Reusable visual treatment marking content that comes from the seeded
// Brookside Meadows case-study fixture rather than a connected backend or a
// real municipal submission. Use it anywhere seeded records render so a
// visitor never mistakes demo data for live operational data.
export default function DemoDataBadge({
  label = "Seeded demo data",
}: {
  label?: string;
}) {
  return (
    <span
      data-testid="demo-data-badge"
      className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-[11px] font-medium text-amber-800"
    >
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-amber-500" />
      {label}
    </span>
  );
}
