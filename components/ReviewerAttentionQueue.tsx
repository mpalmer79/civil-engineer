"use client";

import { useMemo, useState } from "react";
import type { ReviewerAttentionItem } from "@/lib/api";
import AttentionItemCard from "@/components/AttentionItemCard";

const SEVERITY_ORDER = ["needs_human_review", "high", "medium", "low", "info"];

// The reviewer attention queue, grouped by severity. Each item deep links into
// its source module and can be marked reviewer_checked, deferred, or
// not_applicable. None of these closes, resolves, or approves anything.
export default function ReviewerAttentionQueue({
  items,
  busy,
  onStatusChange,
  onSelect,
}: {
  items: ReviewerAttentionItem[];
  busy: boolean;
  onStatusChange: (attentionItemId: string, status: string) => void;
  onSelect?: (item: ReviewerAttentionItem) => void;
}) {
  const [moduleFilter, setModuleFilter] = useState<string>("all");

  const modules = useMemo(
    () => ["all", ...Array.from(new Set(items.map((i) => i.sourceModule)))],
    [items],
  );

  const filtered = useMemo(
    () =>
      moduleFilter === "all"
        ? items
        : items.filter((i) => i.sourceModule === moduleFilter),
    [items, moduleFilter],
  );

  const grouped = useMemo(() => {
    const groups: Record<string, ReviewerAttentionItem[]> = {};
    for (const item of filtered) {
      (groups[item.severity] ??= []).push(item);
    }
    return groups;
  }, [filtered]);

  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">
          Reviewer attention queue
        </h3>
        <select
          value={moduleFilter}
          onChange={(e) => setModuleFilter(e.target.value)}
          className="rounded-md border border-slate-300 px-2 py-1 text-xs"
        >
          {modules.map((m) => (
            <option key={m} value={m}>
              {m === "all" ? "All modules" : m.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        What needs attention right now, grouped by severity. Each item links into
        its module. Marking an item is review-support tracking, not a final
        decision.
      </p>
      {filtered.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No open attention items in this view.
        </p>
      ) : (
        <div className="mt-4 space-y-5">
          {SEVERITY_ORDER.filter((s) => grouped[s]?.length).map((severity) => (
            <div key={severity}>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {severity.replace(/_/g, " ")} ({grouped[severity].length})
              </p>
              <ul className="mt-2 space-y-2">
                {grouped[severity].map((item) => (
                  <AttentionItemCard
                    key={item.attentionItemId}
                    item={item}
                    busy={busy}
                    onStatusChange={onStatusChange}
                    onSelect={onSelect}
                  />
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
