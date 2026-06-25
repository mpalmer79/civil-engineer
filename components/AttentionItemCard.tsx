"use client";

import Link from "next/link";
import type { ReviewerAttentionItem } from "@/lib/api";

const severityStyles: Record<string, string> = {
  info: "bg-slate-100 text-slate-600",
  low: "bg-slate-100 text-slate-600",
  medium: "bg-amber-50 text-amber-700",
  high: "bg-red-50 text-red-700",
  needs_human_review: "bg-amber-50 text-amber-700",
};

const ATTENTION_STATUSES = ["open", "reviewer_checked", "deferred", "not_applicable"];

// A single reviewer attention item with its recommended next step, a deep link
// into the source module, and a status control. Marking an item does not close,
// resolve, or approve anything.
export default function AttentionItemCard({
  item,
  busy,
  onStatusChange,
  onSelect,
}: {
  item: ReviewerAttentionItem;
  busy: boolean;
  onStatusChange: (attentionItemId: string, status: string) => void;
  onSelect?: (item: ReviewerAttentionItem) => void;
}) {
  return (
    <li className="rounded-lg border border-slate-200 px-3 py-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <button
          type="button"
          onClick={() => onSelect?.(item)}
          className="text-left text-sm font-semibold text-slate-800 hover:text-water-700"
        >
          {item.title}
        </button>
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] ${
            severityStyles[item.severity] ?? severityStyles.low
          }`}
        >
          {item.severity.replace(/_/g, " ")}
        </span>
      </div>
      <p className="mt-1 text-xs text-slate-500">
        {item.sourceModule.replace(/_/g, " ")}
      </p>
      <p className="mt-1 text-sm text-slate-600">{item.recommendedNextStep}</p>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <Link
          href={item.targetRoute}
          className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-water-700 transition-colors hover:bg-slate-50"
        >
          Open module
        </Link>
        <select
          value={item.status}
          onChange={(e) => onStatusChange(item.attentionItemId, e.target.value)}
          disabled={busy}
          className="rounded-md border border-slate-300 px-2 py-1 text-xs"
        >
          {ATTENTION_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </div>
    </li>
  );
}
