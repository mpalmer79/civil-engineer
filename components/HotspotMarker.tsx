import type { Hotspot, HotspotCategory } from "@/data/hotspots";

const categoryRing: Record<HotspotCategory, string> = {
  stormwater: "bg-water-600 ring-water-600/30",
  wetland: "bg-teal-600 ring-teal-600/30",
  roadway: "bg-slate-600 ring-slate-600/30",
  erosion_control: "bg-land-600 ring-land-600/30",
  utility: "bg-indigo-600 ring-indigo-600/30",
  lots: "bg-sky-600 ring-sky-600/30",
  risk: "bg-red-600 ring-red-600/30",
};

export default function HotspotMarker({
  hotspot,
  index,
  active,
  onSelect,
}: {
  hotspot: Hotspot;
  index: number;
  active: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(hotspot.id)}
      onMouseEnter={() => onSelect(hotspot.id)}
      onFocus={() => onSelect(hotspot.id)}
      aria-label={`Hotspot ${index}: ${hotspot.name}`}
      aria-pressed={active}
      className="group absolute -translate-x-1/2 -translate-y-1/2 focus:outline-none"
      style={{
        left: `${hotspot.position.xPercent}%`,
        top: `${hotspot.position.yPercent}%`,
      }}
    >
      <span
        className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white ring-4 transition-transform group-hover:scale-110 group-focus-visible:scale-110 ${
          categoryRing[hotspot.category]
        } ${active ? "scale-110 ring-8" : ""}`}
      >
        {index}
      </span>
    </button>
  );
}
