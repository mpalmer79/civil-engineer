"use client";

import { useState } from "react";
import { hotspots } from "@/data/hotspots";
import HotspotMarker from "@/components/HotspotMarker";

const categoryLabel: Record<string, string> = {
  stormwater: "Stormwater",
  wetland: "Wetland",
  roadway: "Roadway",
  erosion_control: "Erosion control",
  utility: "Utility",
  lots: "Lots",
  risk: "Review risk",
};

export default function HeroMap() {
  const [activeId, setActiveId] = useState<string>(hotspots[0].id);
  const active = hotspots.find((h) => h.id === activeId) ?? hotspots[0];

  return (
    <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
      {/* Map image with overlay markers */}
      <figure className="surface-card overflow-hidden p-0">
        <div className="relative aspect-[16/10] w-full bg-gradient-to-br from-land-50 via-water-50 to-slate-100">
          {/* Base image. If development.png is absent, the gradient + label
              below remain visible so the layout never breaks. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/development.png"
            alt="Illustrative site map of the Brookside Meadows subdivision fixture, showing the wooded upland, meadow, stream corridor, proposed roads, lots, and stormwater facilities. Numbered markers indicate interactive review hotspots."
            className="absolute inset-0 h-full w-full object-cover"
          />

          {/* Fallback caption shown behind the image (visible only if the image
              fails to load, since the image sits above it). */}
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center px-6 text-center">
            <span className="text-sm font-medium text-slate-400">
              Brookside Meadows development map
            </span>
          </div>

          {hotspots.map((h, i) => (
            <HotspotMarker
              key={h.id}
              hotspot={h}
              index={i + 1}
              active={h.id === activeId}
              onSelect={setActiveId}
            />
          ))}
        </div>
        <figcaption className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-slate-200 px-4 py-3 text-xs text-slate-500">
          <span className="font-medium text-slate-700">
            Interactive development map
          </span>
          <span>
            Hover, focus, or select a numbered marker to inspect a site feature.
          </span>
        </figcaption>
      </figure>

      {/* Side panel that updates on hotspot selection */}
      <aside
        aria-live="polite"
        className="surface-card flex flex-col p-6"
      >
        <span className="badge w-fit bg-water-50 text-water-700 ring-water-600/20">
          {categoryLabel[active.category] ?? active.category}
        </span>
        <h3 className="mt-3 text-lg font-semibold text-slate-900">
          {active.name}
        </h3>
        <p className="mt-2 text-sm text-slate-600">{active.shortDescription}</p>

        <dl className="mt-4 space-y-3 text-sm">
          <div>
            <dt className="font-semibold text-slate-700">Civil purpose</dt>
            <dd className="mt-0.5 text-slate-600">{active.civilPurpose}</dd>
          </div>
          {active.relatedPlantedIssues.length > 0 ? (
            <div>
              <dt className="font-semibold text-slate-700">
                Related review issues
              </dt>
              <dd className="mt-1 flex flex-wrap gap-1.5">
                {active.relatedPlantedIssues.map((issue) => (
                  <span
                    key={issue}
                    className="badge bg-amber-50 text-amber-700 ring-amber-600/20"
                  >
                    {issue}
                  </span>
                ))}
              </dd>
            </div>
          ) : null}
          <div>
            <dt className="font-semibold text-slate-700">
              Future drill-down (later phases)
            </dt>
            <dd className="mt-0.5 text-slate-600">{active.futureDrilldown}</dd>
          </div>
        </dl>

        <p className="mt-auto pt-4 text-xs text-slate-400">
          Phase 1 shows static hotspot context. Later phases link each marker to
          documents, checklist items, and findings.
        </p>
      </aside>
    </div>
  );
}
