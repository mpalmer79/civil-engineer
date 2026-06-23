import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import { getPlanSheets, getPlanSheetSummary } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  current: "bg-land-50 text-land-700 ring-land-600/20",
  present: "bg-land-50 text-land-700 ring-land-600/20",
  referenced_not_included: "bg-red-50 text-red-700 ring-red-600/20",
  missing: "bg-red-50 text-red-700 ring-red-600/20",
  superseded: "bg-slate-100 text-slate-600 ring-slate-300",
  needs_reviewer_confirmation: "bg-yellow-50 text-yellow-700 ring-yellow-600/20",
};

const CORE_REVIEW_DISCIPLINES = new Set([
  "grading",
  "drainage",
  "utility",
  "erosion_control",
  "details",
]);

function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? "bg-slate-100 text-slate-600 ring-slate-300";
  return <span className={`badge ${style}`}>{status.replace(/_/g, " ")}</span>;
}

export default async function PlanSheetsPage() {
  const [sheets, summary] = await Promise.all([
    getPlanSheets(),
    getPlanSheetSummary(),
  ]);

  return (
    <div>
      <PageHeader
        eyebrow="Plan sheet index"
        title="Brookside Meadows plan sheet index"
        description="Phase 6 adds plan sheet intelligence. This index organizes the civil plan set as review-support metadata, connects each sheet to documents, checklist items, and findings, and flags sheets that are referenced but not included. It does not parse CAD files or approve drawings."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        {summary ? (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
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
              value={summary.missingOrReferencedNotIncludedSheets}
              label="Missing or referenced not included"
              accent={
                summary.missingOrReferencedNotIncludedSheets > 0
                  ? "red"
                  : "land"
              }
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
        ) : (
          <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
            The backend is not reachable. Start the API to load the plan sheet
            index. Plan sheets are backend-canonical and are not duplicated in
            the browser.
          </div>
        )}

        {sheets.length > 0 ? (
          <div className="surface-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Sheet</th>
                    <th className="px-4 py-3">Title</th>
                    <th className="px-4 py-3">Discipline</th>
                    <th className="px-4 py-3">Rev</th>
                    <th className="px-4 py-3">Rev date</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Related</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sheets.map((s) => (
                    <tr
                      key={s.sheetId}
                      className={`hover:bg-slate-50 ${
                        s.status === "referenced_not_included"
                          ? "bg-red-50/40"
                          : ""
                      }`}
                    >
                      <td className="px-4 py-3">
                        <div className="font-mono font-semibold text-slate-900">
                          {s.sheetNumber}
                        </div>
                        {CORE_REVIEW_DISCIPLINES.has(s.discipline) ? (
                          <span className="mt-1 inline-block badge bg-water-50 text-water-700 ring-water-600/20">
                            core civil review
                          </span>
                        ) : null}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900">
                          {s.sheetTitle}
                        </div>
                        <div className="text-xs text-slate-500">
                          {s.sheetPurpose}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {s.discipline.replace(/_/g, " ")}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {s.revision ?? "-"}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {s.revisionDate ?? "-"}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={s.status} />
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">
                        <div>docs: {s.relatedDocuments.length}</div>
                        <div>checklist: {s.relatedChecklistItems.length}</div>
                        <div>findings: {s.relatedFindings.length}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        <SectionCard title="Referenced but not included">
          <p className="text-sm text-slate-600">
            Sheet C-3.1 (Revised Grading and Drainage Plan) is cited by the site
            plan narrative and the stormwater report but is not included in the
            submitted package. It is flagged as referenced not included so a
            reviewer can request it. This is a potential issue that requires
            reviewer confirmation, not a final determination.
          </p>
        </SectionCard>

        <SafetyBoundaryBanner />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Phase 6 note:</span>{" "}
          The plan sheet index is seeded CAD-aware metadata, not parsed CAD
          files. See the{" "}
          <a
            href="/cad-review"
            className="font-semibold text-water-700 hover:text-water-600"
          >
            CAD Review
          </a>{" "}
          page for civil feature metadata and plan consistency checks.
        </div>
      </div>
    </div>
  );
}
