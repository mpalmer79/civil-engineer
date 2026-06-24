import type { WorkflowItem } from "@/lib/api";
import WorkflowItemCard from "@/components/WorkflowItemCard";

// One status column on the reviewer workflow board. Columns describe workflow
// position, not an approval or certification state.
export default function WorkflowColumn({
  label,
  status,
  items,
  selectedItemId,
  onSelectItem,
}: {
  label: string;
  status: string;
  items: WorkflowItem[];
  selectedItemId: string | null;
  onSelectItem: (workflowItemId: string) => void;
}) {
  const columnItems = items.filter((i) => i.status === status);
  return (
    <div className="flex w-72 flex-shrink-0 flex-col rounded-xl bg-slate-50 p-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-700">{label}</p>
        <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium text-slate-500">
          {columnItems.length}
        </span>
      </div>
      <div className="mt-3 space-y-2">
        {columnItems.length === 0 ? (
          <p className="rounded-lg border border-dashed border-slate-200 px-3 py-4 text-center text-xs text-slate-400">
            No items
          </p>
        ) : (
          columnItems.map((item) => (
            <WorkflowItemCard
              key={item.workflowItemId}
              item={item}
              selected={item.workflowItemId === selectedItemId}
              onSelect={onSelectItem}
            />
          ))
        )}
      </div>
    </div>
  );
}
