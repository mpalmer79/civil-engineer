"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  generateReviewPacket,
  getReviewPacket,
  getReviewPackets,
  getReviewPacketSummary,
  type ReviewPacketDetail,
  type ReviewPacketItem,
  type ReviewPacketSummary,
} from "@/lib/api";
import ReviewPacketSummaryCard from "@/components/ReviewPacketSummaryCard";
import ReviewPacketSectionList from "@/components/ReviewPacketSectionList";
import ReviewPacketItemPanel from "@/components/ReviewPacketItemPanel";
import ReviewPacketActionPanel from "@/components/ReviewPacketActionPanel";
import EvidenceTraceabilityMatrix from "@/components/EvidenceTraceabilityMatrix";
import ReviewPacketPrintPreview from "@/components/ReviewPacketPrintPreview";
import ProfessionalLimitationsNotice from "@/components/ProfessionalLimitationsNotice";

type Tab = "sections" | "traceability" | "print";

// Orchestrates the review packet experience: generate or load the packet, show
// its sections and items, the linked evidence, the traceability matrix, the
// reviewer action form, and the printable preview.
export default function ReviewPacketBuilder({
  packetId,
  projectId,
}: {
  packetId?: string;
  projectId?: string;
}) {
  const [packet, setPacket] = useState<ReviewPacketDetail | null>(null);
  const [summary, setSummary] = useState<ReviewPacketSummary | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [reviewerName, setReviewerName] = useState("Town Engineer");
  const [tab, setTab] = useState<Tab>("sections");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const loadPacket = useCallback(async (id: string) => {
    const [detail, sum] = await Promise.all([
      getReviewPacket(id),
      getReviewPacketSummary(id),
    ]);
    setPacket(detail);
    setSummary(sum);
    if (detail && detail.sections.length > 0) {
      const firstWithItems = detail.sections.find((s) => s.items.length > 0);
      if (firstWithItems) setSelectedItemId(firstWithItems.items[0].itemId);
    }
  }, []);

  useEffect(() => {
    (async () => {
      if (packetId) {
        await loadPacket(packetId);
      } else {
        const packets = await getReviewPackets(projectId);
        if (packets.length > 0) {
          await loadPacket(packets[0].packetId);
        }
      }
      setLoaded(true);
    })();
  }, [packetId, loadPacket, projectId]);

  const handleGenerate = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await generateReviewPacket(projectId);
    if (result.ok && result.packet) {
      setPacket(result.packet);
      setSummary(await getReviewPacketSummary(result.packet.packetId));
      const firstWithItems = result.packet.sections.find(
        (s) => s.items.length > 0,
      );
      setSelectedItemId(firstWithItems ? firstWithItems.items[0].itemId : null);
      setMessage("Review packet draft generated.");
    } else {
      setMessage(result.error ?? "Could not generate the review packet.");
    }
    setBusy(false);
  }, [projectId]);

  const handleItemUpdated = useCallback(
    (updated: ReviewPacketItem) => {
      setPacket((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          sections: prev.sections.map((s) => ({
            ...s,
            items: s.items.map((i) =>
              i.itemId === updated.itemId ? updated : i,
            ),
          })),
        };
      });
      if (packet) {
        getReviewPacketSummary(packet.packetId).then(setSummary);
      }
    },
    [packet],
  );

  const selectedItem = useMemo(() => {
    if (!packet) return null;
    for (const section of packet.sections) {
      const found = section.items.find((i) => i.itemId === selectedItemId);
      if (found) return found;
    }
    return null;
  }, [packet, selectedItemId]);

  if (loaded && !packet) {
    return (
      <div className="space-y-4">
        <ProfessionalLimitationsNotice />
        <div className="surface-card p-6">
          <p className="text-sm text-slate-600">
            No review packet is loaded yet. Generate a review-support packet
            draft for this project to begin.
          </p>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={busy}
            className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Generating..." : "Generate review packet"}
          </button>
          {message ? (
            <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
              {message}
            </p>
          ) : null}
        </div>
      </div>
    );
  }

  if (!packet) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Loading review packet...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ProfessionalLimitationsNotice />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {(["sections", "traceability", "print"] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors ${
                tab === t
                  ? "bg-water-600 text-white"
                  : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              {t === "sections"
                ? "Sections and items"
                : t === "traceability"
                  ? "Traceability matrix"
                  : "Printable summary"}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={handleGenerate}
          disabled={busy}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
        >
          {busy ? "Regenerating..." : "Regenerate draft"}
        </button>
      </div>

      {message ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {message}
        </p>
      ) : null}

      <ReviewPacketSummaryCard packet={packet} summary={summary} />

      {tab === "sections" ? (
        <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <ReviewPacketSectionList
            sections={packet.sections}
            selectedItemId={selectedItemId}
            onSelectItem={setSelectedItemId}
          />
          <div className="space-y-6">
            <ReviewPacketItemPanel item={selectedItem} />
            <ReviewPacketActionPanel
              packetId={packet.packetId}
              item={selectedItem}
              reviewerName={reviewerName}
              onReviewerNameChange={setReviewerName}
              onItemUpdated={handleItemUpdated}
            />
          </div>
        </div>
      ) : null}

      {tab === "traceability" ? (
        <EvidenceTraceabilityMatrix packetId={packet.packetId} />
      ) : null}

      {tab === "print" ? (
        <ReviewPacketPrintPreview packetId={packet.packetId} />
      ) : null}
    </div>
  );
}
