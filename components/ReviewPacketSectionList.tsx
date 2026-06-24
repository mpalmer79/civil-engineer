"use client";

import type { ReviewPacketSection } from "@/lib/api";
import PlanStatusBadge from "@/components/PlanStatusBadge";

const SEVERITY_DOT: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-water-500",
  info: "bg-slate-300",
};

// Lists packet sections and their items. Selecting an item raises onSelectItem.
export default function ReviewPacketSectionList({
  sections,
  selectedItemId,
  onSelectItem,
}: {
  sections: ReviewPacketSection[];
  selectedItemId: string | null;
  onSelectItem: (itemId: string) => void;
}) {
  return (
    <div className="space-y-4">
      {sections.map((section) => (
        <div key={section.sectionId} className="surface-card overflow-hidden">
          <div className="border-b border-slate-100 px-4 py-3">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-sm font-semibold text-slate-900">
                {section.title}
              </h3>
              <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                {section.items.length} item
                {section.items.length === 1 ? "" : "s"}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500">{section.summary}</p>
          </div>
          {section.items.length > 0 ? (
            <ul className="divide-y divide-slate-100">
              {section.items.map((item) => (
                <li key={item.itemId}>
                  <button
                    type="button"
                    onClick={() => onSelectItem(item.itemId)}
                    className={`flex w-full items-start gap-2 px-4 py-2 text-left transition-colors hover:bg-slate-50 ${
                      item.itemId === selectedItemId ? "bg-slate-100" : ""
                    }`}
                  >
                    <span
                      aria-hidden="true"
                      className={`mt-1.5 h-2 w-2 flex-none rounded-full ${
                        SEVERITY_DOT[item.severity] ?? "bg-slate-300"
                      }`}
                    />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm text-slate-800">
                        {item.title}
                      </span>
                      <span className="mt-0.5 flex items-center gap-2">
                        <PlanStatusBadge status={item.reviewerStatus} />
                        <span className="text-xs text-slate-400">
                          {item.itemType.replace(/_/g, " ")}
                        </span>
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="px-4 py-3 text-xs text-slate-400">
              No items in this section.
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
