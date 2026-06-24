"use client";

import type { ReviewPacketDetail, ReviewPacketSummary } from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import PlanStatusBadge from "@/components/PlanStatusBadge";

export default function ReviewPacketSummaryCard({
  packet,
  summary,
}: {
  packet: ReviewPacketDetail;
  summary: ReviewPacketSummary | null;
}) {
  return (
    <div className="space-y-4">
      <div className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              {packet.title}
            </h2>
            <p className="mt-1 font-mono text-xs text-slate-400">
              {packet.packetId}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
              {packet.packetType.replace(/_/g, " ")}
            </span>
            <PlanStatusBadge status={packet.status} />
          </div>
        </div>
        <p className="mt-3 text-sm text-slate-600">{packet.summary}</p>
        <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">
          {packet.limitationsNote}
        </p>
      </div>

      {summary ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <MetricCard
            value={summary.totalSections}
            label="Packet sections"
            accent="water"
          />
          <MetricCard
            value={summary.totalItems}
            label="Packet items"
            accent="water"
          />
          <MetricCard
            value={summary.totalEvidenceLinks}
            label="Evidence links"
            accent="land"
          />
          <MetricCard
            value={summary.itemsRequiringHumanReview}
            label="Items needing human review"
            accent="amber"
          />
        </div>
      ) : null}
    </div>
  );
}
