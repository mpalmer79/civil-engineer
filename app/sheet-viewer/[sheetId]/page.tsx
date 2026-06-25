import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import PlanSheetViewer from "@/components/PlanSheetViewer";

export default function SheetViewerDetailPage({
  params,
}: {
  params: { sheetId: string };
}) {
  return (
    <div>
      <PageHeader
        eyebrow="Plan sheet viewer"
        title="Sheet review"
        description="Select a numbered hotspot to inspect its connected plan references, CAD-aware metadata, documents, checklist items, and plan consistency findings, and to record a review-support action. The preview and hotspots are seeded review-support metadata, not extracted CAD or verified plan geometry."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <Link
          href="/sheet-viewer"
          className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
        >
          Back to all sheets
        </Link>

        <PlanSheetViewer sheetId={params.sheetId} />

        <SafetyBoundaryBanner />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Note:</span>{" "}
          Plan consistency review actions are persisted by the backend. No action
          approves a plan, certifies compliance, verifies CAD, or validates a
          design.
        </div>
      </div>
    </div>
  );
}
