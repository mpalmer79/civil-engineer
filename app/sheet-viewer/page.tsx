import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import PlanStatusBadge from "@/components/PlanStatusBadge";
import { getPlanSheets, getSheetHotspots } from "@/lib/api";

export default async function SheetViewerPage() {
  const [sheets, hotspots] = await Promise.all([
    getPlanSheets(),
    getSheetHotspots(),
  ]);

  const hotspotCountBySheet: Record<string, number> = {};
  for (const h of hotspots) {
    hotspotCountBySheet[h.sheetId] = (hotspotCountBySheet[h.sheetId] ?? 0) + 1;
  }

  return (
    <div>
      <PageHeader
        eyebrow="Plan sheet viewer"
        title="Open a Brookside Meadows plan sheet"
        description="Civil Engineer AI adds a reviewer-facing plan sheet viewer. Select a sheet to see seeded hotspot annotations over a synthetic preview and inspect connected plan references, CAD-aware metadata, documents, checklist items, and plan consistency findings. The preview and hotspots are seeded review-support metadata. Real DXF upload and metadata extraction happen in CAD Intake; the viewer does not extract CAD geometry or verify plan geometry."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SafetyBoundaryBanner variant="compact" />

        {sheets.length === 0 ? (
          <div className="surface-card p-6">
            <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
              The backend is required to load the plan sheet index. Start the API
              to open the seeded Brookside Meadows plan sheets.
            </p>
          </div>
        ) : (
          <SectionCard
            title="Plan sheets"
            description="Sheets with seeded hotspots are highlighted. Open a sheet to review its hotspots in place."
          >
            <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {sheets.map((s) => {
                const count = hotspotCountBySheet[s.sheetId] ?? 0;
                return (
                  <li key={s.sheetId}>
                    <Link
                      href={`/sheet-viewer/${s.sheetId}`}
                      className="block h-full rounded-lg border border-slate-200 p-4 transition-colors hover:border-water-300 hover:bg-slate-50"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono text-sm font-semibold text-slate-900">
                          {s.sheetNumber}
                        </span>
                        <PlanStatusBadge status={s.status} />
                      </div>
                      <div className="mt-1 text-sm font-medium text-slate-800">
                        {s.sheetTitle}
                      </div>
                      <div className="mt-2 text-xs text-slate-500">
                        {s.discipline.replace(/_/g, " ")}
                      </div>
                      <div className="mt-3">
                        {count > 0 ? (
                          <span className="badge bg-water-50 text-water-700 ring-water-600/20">
                            {count} hotspot{count === 1 ? "" : "s"}
                          </span>
                        ) : (
                          <span className="badge bg-slate-100 text-slate-500 ring-slate-300">
                            no hotspots
                          </span>
                        )}
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </SectionCard>
        )}

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Note:</span>{" "}
          The sheet viewer preview is a synthetic image with seeded
          review-support hotspots; it does not render real PDF or parse DWG or
          Autodesk data. Real DXF upload and metadata extraction happen in CAD
          Intake. The viewer does not verify CAD, certify compliance, or replace
          a licensed engineer.
        </div>
      </div>
    </div>
  );
}
