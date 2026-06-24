"use client";

import type { PlanSheetHotspot } from "@/lib/api";

const SEVERITY_RING: Record<string, string> = {
  high: "border-red-500/80 bg-red-500/10 hover:bg-red-500/20",
  medium: "border-amber-500/80 bg-amber-500/10 hover:bg-amber-500/20",
  low: "border-water-500/80 bg-water-500/10 hover:bg-water-500/20",
};

// Renders the seeded hotspots as absolutely positioned annotation regions over
// the synthetic sheet preview. Coordinates are percentages of the preview
// surface, so the overlay scales with the preview.
export default function SheetHotspotOverlay({
  hotspots,
  selectedId,
  onSelect,
}: {
  hotspots: PlanSheetHotspot[];
  selectedId: string | null;
  onSelect: (hotspotId: string) => void;
}) {
  return (
    <div className="pointer-events-none absolute inset-0">
      {hotspots.map((h, index) => {
        const ring = SEVERITY_RING[h.severity] ?? SEVERITY_RING.low;
        const isSelected = h.hotspotId === selectedId;
        return (
          <button
            key={h.hotspotId}
            type="button"
            onClick={() => onSelect(h.hotspotId)}
            aria-label={`Hotspot: ${h.label}`}
            className={`pointer-events-auto absolute flex items-start justify-start rounded-md border-2 ${ring} ${
              isSelected ? "ring-2 ring-water-600 ring-offset-1" : ""
            } transition-colors`}
            style={{
              left: `${h.xPercent}%`,
              top: `${h.yPercent}%`,
              width: `${h.widthPercent}%`,
              height: `${h.heightPercent}%`,
            }}
          >
            <span className="m-1 rounded bg-white/90 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700 shadow-sm">
              {index + 1}
            </span>
          </button>
        );
      })}
    </div>
  );
}
