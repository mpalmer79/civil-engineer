// A small badge distinguishing the seeded Brookside Meadows demo fixture from
// real, user-created project records and documents.
export default function SourceBadge({ sourceMode }: { sourceMode: string }) {
  const isDemo = sourceMode === "demo_fixture";
  const label = isDemo
    ? "Demo fixture"
    : sourceMode === "user_uploaded"
      ? "User-uploaded"
      : sourceMode === "user_registered"
        ? "User-registered"
        : "User-created";
  const classes = isDemo
    ? "bg-slate-100 text-slate-600 ring-slate-200"
    : "bg-water-50 text-water-700 ring-water-200";
  return (
    <span className={`badge ring-1 ${classes}`} data-source-mode={sourceMode}>
      {label}
    </span>
  );
}
