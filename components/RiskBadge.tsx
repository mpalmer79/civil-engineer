import type { ChecklistRisk } from "@/data/checklist";

const styles: Record<ChecklistRisk, string> = {
  high: "bg-red-50 text-red-700 ring-red-600/20",
  medium: "bg-amber-50 text-amber-700 ring-amber-600/20",
  low: "bg-slate-100 text-slate-600 ring-slate-300",
};

export default function RiskBadge({ level }: { level: ChecklistRisk }) {
  return (
    <span className={`badge ${styles[level]}`}>
      <span aria-hidden="true" className="text-[10px]">
        ●
      </span>
      {level} risk
    </span>
  );
}
