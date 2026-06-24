"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getSheetViewerContext,
  type PlanConsistencyFinding,
  type SheetViewerContext,
} from "@/lib/api";
import PlanStatusBadge from "@/components/PlanStatusBadge";
import SheetHotspotOverlay from "@/components/SheetHotspotOverlay";
import SheetHotspotPanel from "@/components/SheetHotspotPanel";
import SheetReferencePanel from "@/components/SheetReferencePanel";
import PlanFindingReviewPanel from "@/components/PlanFindingReviewPanel";

// The reviewer-facing plan sheet viewer. It loads the seeded viewer context for
// one sheet, renders a synthetic plan sheet preview with hotspot annotations,
// and lets the reviewer inspect connected evidence and record review actions on
// plan consistency findings. The preview and hotspots are seeded review-support
// metadata, not extracted CAD or verified plan geometry.
export default function PlanSheetViewer({ sheetId }: { sheetId: string }) {
  const [context, setContext] = useState<SheetViewerContext | null>(null);
  const [findings, setFindings] = useState<PlanConsistencyFinding[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reviewerName, setReviewerName] = useState("Town Engineer");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      const ctx = await getSheetViewerContext(sheetId);
      setContext(ctx);
      setFindings(ctx ? ctx.planConsistencyFindings : []);
      if (ctx && ctx.hotspots.length > 0) {
        setSelectedId(ctx.hotspots[0].hotspotId);
      }
      setLoaded(true);
    })();
  }, [sheetId]);

  const handleActionRecorded = useCallback(
    (updated: PlanConsistencyFinding) => {
      setFindings((prev) =>
        prev.map((f) =>
          f.planFindingId === updated.planFindingId ? updated : f,
        ),
      );
    },
    [],
  );

  const selectedHotspot = useMemo(
    () =>
      context?.hotspots.find((h) => h.hotspotId === selectedId) ?? null,
    [context, selectedId],
  );
  const selectedIndex = useMemo(
    () =>
      context
        ? context.hotspots.findIndex((h) => h.hotspotId === selectedId)
        : -1,
    [context, selectedId],
  );

  if (loaded && !context) {
    return (
      <div className="surface-card p-6">
        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
          The backend is required to load the sheet viewer. Start the API to
          view the seeded Brookside Meadows plan sheet and its hotspots. Hotspot
          and review data are not simulated in the browser.
        </p>
      </div>
    );
  }

  if (!context) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Loading sheet viewer...
      </div>
    );
  }

  const { sheet } = context;

  return (
    <div className="space-y-6">
      <div className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">
        {context.previewNote}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        {/* Synthetic sheet preview with hotspot overlay */}
        <div>
          <div className="surface-card overflow-hidden p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3">
              <div>
                <span className="font-mono text-sm font-semibold text-slate-900">
                  {sheet.sheetNumber}
                </span>
                <span className="ml-2 text-sm text-slate-600">
                  {sheet.sheetTitle}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                  Rev {sheet.revision}
                </span>
                <PlanStatusBadge status={sheet.status} />
              </div>
            </div>

            {/* Faux plan sheet surface. The grid background and titleblock make
                it read as a sheet without being a real drawing. */}
            <div
              className="relative w-full overflow-hidden rounded-md border border-slate-300 bg-white"
              style={{
                aspectRatio: "11 / 8.5",
                backgroundImage:
                  "linear-gradient(to right, rgba(148,163,184,0.18) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.18) 1px, transparent 1px)",
                backgroundSize: "7% 9%",
              }}
            >
              <div className="absolute inset-x-0 top-0 flex items-center justify-between border-b border-dashed border-slate-300 bg-slate-50/80 px-3 py-1 text-[10px] uppercase tracking-wide text-slate-400">
                <span>Brookside Meadows</span>
                <span>Seeded preview, not a real drawing</span>
              </div>
              <div className="absolute bottom-0 right-0 m-2 w-40 rounded border border-slate-300 bg-white/90 p-2 text-[10px] text-slate-500">
                <div className="font-semibold text-slate-700">
                  {sheet.sheetNumber}
                </div>
                <div>{sheet.sheetTitle}</div>
                <div className="mt-1 text-slate-400">
                  {sheet.discipline.replace(/_/g, " ")}
                </div>
              </div>

              <SheetHotspotOverlay
                hotspots={context.hotspots}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            </div>

            <p className="mt-3 text-xs text-slate-500">
              {sheet.sheetPurpose}
            </p>
          </div>

          {/* Hotspot legend */}
          {context.hotspots.length > 0 ? (
            <div className="surface-card mt-4 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Hotspots on this sheet
              </p>
              <ul className="mt-2 space-y-1">
                {context.hotspots.map((h, i) => (
                  <li key={h.hotspotId}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(h.hotspotId)}
                      className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-sm transition-colors hover:bg-slate-50 ${
                        h.hotspotId === selectedId ? "bg-slate-100" : ""
                      }`}
                    >
                      <span className="flex h-5 w-5 flex-none items-center justify-center rounded-full bg-water-600 text-[11px] font-bold text-white">
                        {i + 1}
                      </span>
                      <span className="text-slate-700">{h.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="surface-card mt-4 p-4 text-sm text-slate-500">
              No hotspots are seeded on this sheet.
            </p>
          )}
        </div>

        {/* Detail and review panels */}
        <div className="space-y-6">
          <SheetHotspotPanel
            hotspot={selectedHotspot}
            index={selectedIndex >= 0 ? selectedIndex : null}
          />
          <SheetReferencePanel
            hotspot={selectedHotspot}
            cadMetadata={context.cadMetadata}
            planReferences={context.planReferences}
          />
          <PlanFindingReviewPanel
            hotspot={selectedHotspot}
            findings={findings}
            reviewerName={reviewerName}
            onReviewerNameChange={setReviewerName}
            onActionRecorded={handleActionRecorded}
          />
        </div>
      </div>
    </div>
  );
}
