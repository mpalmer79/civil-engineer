"use client";

import Link from "next/link";
import type { ReviewerAttentionItem } from "@/lib/api";

// A detail view of a selected reviewer attention item. Read-only context plus a
// deep link into the source module. Marking status happens on the card.
export default function AttentionItemDetailPanel({
  item,
}: {
  item: ReviewerAttentionItem | null;
}) {
  if (!item) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Select an attention item to see its detail and recommended next step.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">{item.title}</h3>
      <p className="mt-1 text-xs text-slate-500">
        {item.attentionType.replace(/_/g, " ")} ·{" "}
        {item.sourceModule.replace(/_/g, " ")}
      </p>
      <p className="mt-3 text-sm text-slate-600">{item.description}</p>
      <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Recommended next step
        </p>
        <p className="mt-1 text-sm text-slate-700">{item.recommendedNextStep}</p>
      </div>
      <Link
        href={item.targetRoute}
        className="mt-3 inline-block rounded-lg bg-water-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-water-700"
      >
        Open {item.sourceModule.replace(/_/g, " ")}
      </Link>
    </div>
  );
}
