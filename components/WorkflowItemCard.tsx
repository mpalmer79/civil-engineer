import type { WorkflowItem } from "@/lib/api";

const severityStyles: Record<string, string> = {
  high: "text-red-700",
  medium: "text-amber-700",
  low: "text-slate-500",
  info: "text-slate-500",
};

// A compact card representing one workflow item in a board column.
export default function WorkflowItemCard({
  item,
  selected,
  onSelect,
}: {
  item: WorkflowItem;
  selected: boolean;
  onSelect: (workflowItemId: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(item.workflowItemId)}
      className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
        selected
          ? "border-water-500 bg-water-50"
          : "border-slate-200 bg-white hover:bg-slate-50"
      }`}
    >
      <p className="text-sm font-semibold text-slate-800">{item.title}</p>
      <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span className={severityStyles[item.severity] ?? "text-slate-500"}>
          {item.severity}
        </span>
        <span aria-hidden="true">·</span>
        <span>{item.sectionType.replace(/_/g, " ")}</span>
        <span aria-hidden="true">·</span>
        <span>{item.assignedRole.replace(/_/g, " ")}</span>
      </div>
    </button>
  );
}
