// A simple, dependency-free horizontal bar list for showing counts by category
// (for example finding counts by type). Presentational only: the bar widths are
// relative to the largest count and carry no judgment about the data.
export type CountByCategoryItem = {
  label: string;
  count: number;
  tone?: "neutral" | "water" | "amber" | "red";
};

const toneClass: Record<string, string> = {
  neutral: "bg-slate-400",
  water: "bg-water-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
};

export default function CountByCategoryBar({
  items,
  emptyText = "No category counts available.",
}: {
  items: CountByCategoryItem[];
  emptyText?: string;
}) {
  const visible = items.filter((item) => item.count > 0);
  if (visible.length === 0) {
    return <p className="text-sm text-slate-500">{emptyText}</p>;
  }
  const max = Math.max(...visible.map((item) => item.count), 1);
  return (
    <ul className="space-y-2">
      {visible.map((item) => {
        const width = Math.max(6, Math.round((item.count / max) * 100));
        return (
          <li key={item.label} className="text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate-700">{item.label}</span>
              <span className="font-semibold text-slate-900">{item.count}</span>
            </div>
            <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${
                  toneClass[item.tone ?? "neutral"]
                }`}
                style={{ width: `${width}%` }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}
