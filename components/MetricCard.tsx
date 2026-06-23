export default function MetricCard({
  value,
  label,
  hint,
  accent = "slate",
}: {
  value: string | number;
  label: string;
  hint?: string;
  accent?: "slate" | "water" | "land" | "amber" | "red";
}) {
  const accents: Record<string, string> = {
    slate: "text-slate-900",
    water: "text-water-700",
    land: "text-land-700",
    amber: "text-amber-700",
    red: "text-red-700",
  };
  return (
    <div className="surface-card p-5">
      <div className={`text-3xl font-bold tracking-tight ${accents[accent]}`}>
        {value}
      </div>
      <div className="mt-1 text-sm font-medium text-slate-700">{label}</div>
      {hint ? <div className="mt-1 text-xs text-slate-500">{hint}</div> : null}
    </div>
  );
}
