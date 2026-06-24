import type { ResponsePackageSection } from "@/lib/api";

const itemStatusStyles: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600",
  included: "bg-land-50 text-land-700",
  excluded: "bg-slate-100 text-slate-500",
  needs_revision: "bg-amber-50 text-amber-700",
  reviewer_checked: "bg-water-50 text-water-700",
};

// Lists response package sections and their items, allowing item selection.
export default function ResponsePackageSectionList({
  sections,
  selectedItemId,
  onSelectItem,
}: {
  sections: ResponsePackageSection[];
  selectedItemId: string | null;
  onSelectItem: (itemId: string) => void;
}) {
  return (
    <div className="surface-card divide-y divide-slate-100 p-0">
      {sections.map((section) => (
        <div key={section.sectionId} className="p-4">
          <div className="flex items-baseline justify-between gap-2">
            <h4 className="text-sm font-semibold text-slate-800">
              {section.title}
            </h4>
            <span className="text-xs text-slate-400">
              {section.items.length} items
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">{section.summary}</p>
          <ul className="mt-3 space-y-1.5">
            {section.items.map((item) => (
              <li key={item.itemId}>
                <button
                  type="button"
                  onClick={() => onSelectItem(item.itemId)}
                  className={`w-full rounded-lg border px-3 py-2 text-left transition-colors ${
                    item.itemId === selectedItemId
                      ? "border-water-500 bg-water-50"
                      : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-slate-800">
                      {item.title}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[11px] ${
                        itemStatusStyles[item.status] ?? itemStatusStyles.draft
                      }`}
                    >
                      {item.status.replace(/_/g, " ")}
                    </span>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
