import PageHeader from "@/components/PageHeader";
import MetricCard from "@/components/MetricCard";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import PlanStatusBadge from "@/components/PlanStatusBadge";
import { getPlanSheets, getPlanSheetSummary } from "@/lib/api";

const CORE_REVIEW_DISCIPLINES = new Set([
  "grading",
  "drainage",
  "utility",
  "erosion_control",
  "details",
]);

export default async function PlanSheetsPage() {
  const [sheets, summary] = await Promise.all([
    getPlanSheets(),
    getPlanSheetSummary(),
  ]);

  if (sheets.length === 0) {
    return (
      <div>
        <PageHeader
          eyebrow="Plan sheets"
          title="Brookside Meadows plan sheet index"
          description="Phase 6 adds a plan sheet index with sheet metadata, revisions, and missing sheet detection. The plan sheet data is served by the backend."
        />
        <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            The backend is required for the plan sheet index. Start the API to
            load the seeded Brookside Meadows plan set. The plan sheet index is
            not duplicated in the browser.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        eyebrow="Plan sheets"
        title="Brookside Meadows plan sheet index"
        description="Phase 6 organizes plan sheet metadata for review: sheet number, title, discipline, revision, status, and connections to documents, checklist items, and findings. This is plan sheet evidence for a human reviewer, not full CAD parsing or a final design review."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        {summary ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            <MetricCard
              value={summary.totalSheets}
              label="Total sheets"
              accent="water"
            />
            <MetricCard
              value={summary.presentSheets}
              label="Present sheets"
              accent="land"
            />
            <MetricCard
              value={summary.missingOrReferencedNotIncluded}
              label="Missing or referenced, not included"
              accent="red"
            />
            <MetricCard
              value={summary.sheetsWithRelatedFindings}
              label="Sheets with related findings"
              accent="amber"
            />
            <MetricCard
              value={summary.cadMetadataRecords}
              label="CAD-aware metadata records"
              accent="water"
            />
          </div>
        ) : null}

        <SafetyBoundaryBanner variant="compact" />

        <SectionCard title="Plan sheet index">
          <p className="text-sm text-slate-600">
            Sheet C-3.1 is highlighted as referenced but not included. Grading,
            drainage, utility, erosion control, and detail sheets are flagged as
            core civil review sheets.
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Sheet</th>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Discipline</th>
                  <th className="px-4 py-3">Rev</th>
                  <th className="px-4 py-3">Revision date</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Related</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sheets.map((sheet) => {
                  const core = CORE_REVIEW_DISCIPLINES.has(sheet.discipline);
                  const flagged =
                    sheet.status === "referenced_not_included" ||
                    sheet.status === "missing";
                  return (
                    <tr
                      key={sheet.sheetId}
                      className={flagged ? "bg-orange-50/60" : "hover:bg-slate-50"}
                    >
                      <td className="px-4 py-3 font-mono text-xs font-semibold text-slate-800">
                        {sheet.sheetNumber}
                      </td>
                      <td className="px-4 py-3 text-slate-700">
                        {sheet.sheetTitle}
                        <div className="mt-0.5 text-xs text-slate-500">
                          {sheet.sheetPurpose}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-slate-600">
                          {sheet.discipline.replace(/_/g, " ")}
                        </span>
                        {core ? (
                          <span className="ml-2 badge bg-water-50 text-water-700 ring-water-600/20">
                            core review
                          </span>
                        ) : null}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {sheet.revision}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {sheet.revisionDate ?? "-"}
                      </td>
                      <td className="px-4 py-3">
                        <PlanStatusBadge status={sheet.status} />
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">
                        <div>
                          docs: {sheet.relatedDocuments.length} · checklist:{" "}
                          {sheet.relatedChecklistItems.length} · findings:{" "}
                          {sheet.relatedFindings.length}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Scope note:</span>{" "}
          Phase 6 models plan sheet metadata and CAD-aware feature references. It
          does not parse DWG or DXF files, verify CAD drawings, or perform final
          design review. Every plan sheet status keeps the work under human
          review.
        </div>
      </div>
    </div>
  );
}
