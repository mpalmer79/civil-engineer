import type { ReactNode } from "react";

export default function MetricCard({
  value,
  label,
  hint,
  accent = "slate",
  icon,
}: {
  value: string | number;
  label: string;
  hint?: string;
  accent?: "slate" | "water" | "land" | "amber" | "red";
  // Optional decorative corner watermark. Rendered very faintly behind the
  // value so it never competes with the number. Pass an aria-hidden SVG.
  icon?: ReactNode;
}) {
  const accents: Record<string, string> = {
    slate: "text-slate-900",
    water: "text-water-700",
    land: "text-land-700",
    amber: "text-amber-700",
    red: "text-red-700",
  };
  return (
    <div className="surface-card relative overflow-hidden p-5">
      {icon ? (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute right-2 top-2 h-9 w-9 text-slate-400 opacity-[0.18]"
        >
          {icon}
        </span>
      ) : null}
      <div
        className={`relative text-3xl font-bold tracking-tight ${accents[accent]}`}
      >
        {value}
      </div>
      <div className="relative mt-1 text-sm font-medium text-slate-700">
        {label}
      </div>
      {hint ? (
        <div className="relative mt-1 text-xs text-slate-500">{hint}</div>
      ) : null}
    </div>
  );
}
