"use client";

import type { ReviewPacketItem } from "@/lib/api";
import PlanStatusBadge from "@/components/PlanStatusBadge";

const SEVERITY_STYLE: Record<string, string> = {
  high: "bg-red-50 text-red-700 ring-red-600/20",
  medium: "bg-amber-50 text-amber-700 ring-amber-600/20",
  low: "bg-water-50 text-water-700 ring-water-600/20",
  info: "bg-slate-100 text-slate-600 ring-slate-300",
};

// Shows the selected packet item with its source and linked evidence.
export default function ReviewPacketItemPanel({
  item,
}: {
  item: ReviewPacketItem | null;
}) {
  if (!item) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-base font-semibold text-slate-900">Item details</h3>
        <p className="mt-2 text-sm text-slate-600">
          Select a packet item to see its description and linked evidence.
        </p>
      </div>
    );
  }

  const severityStyle =
    SEVERITY_STYLE[item.severity] ?? "bg-slate-100 text-slate-600 ring-slate-300";

  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
          {item.itemType.replace(/_/g, " ")}
        </span>
        <span className={`badge ${severityStyle}`}>{item.severity}</span>
        <PlanStatusBadge status={item.reviewerStatus} />
        {item.requiresHumanReview ? (
          <span className="badge bg-amber-50 text-amber-700 ring-amber-600/20">
            needs human review
          </span>
        ) : null}
      </div>
      <h3 className="mt-3 text-base font-semibold text-slate-900">
        {item.title}
      </h3>
      <p className="mt-2 text-sm text-slate-600">{item.description}</p>
      <p className="mt-2 font-mono text-xs text-slate-400">
        source: {item.sourceType}
        {item.sourceId ? ` / ${item.sourceId}` : ""}
      </p>

      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Linked evidence ({item.evidenceLinks.length})
        </p>
        {item.evidenceLinks.length > 0 ? (
          <ul className="mt-2 space-y-1">
            {item.evidenceLinks.map((link) => (
              <li
                key={link.evidenceLinkId}
                className="rounded-md bg-slate-50 px-3 py-1.5 text-xs text-slate-600"
              >
                <span className="font-semibold text-slate-700">
                  {link.evidenceType.replace(/_/g, " ")}
                </span>{" "}
                <span className="font-mono">{link.evidenceId}</span>
                <span className="text-slate-400">
                  {" "}
                  ({link.relationship.replace(/_/g, " ")})
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-1 text-xs text-slate-400">
            No linked evidence for this item.
          </p>
        )}
      </div>
    </div>
  );
}
