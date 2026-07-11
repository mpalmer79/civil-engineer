import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import RequestFailureCard from "@/components/RequestFailureCard";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import EmptyState from "@/components/EmptyState";
import BoundaryNote from "@/components/BoundaryNote";
import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import {
  getPlanSheets,
  getPlanSheetSummary,
  getProjectDetail,
} from "@/lib/api";

export const dynamic = "force-dynamic";

const SHEETS_BOUNDARY_NOTE =
  "Plan sheets are review-support records of the submitted plan set. This index " +
  "shows recorded sheet metadata only. It does not render drawings and does not " +
  "verify or validate any sheet.";

export default async function PlanSheetIndexPage(
  props: {
    params: Promise<{ projectId: string }>;
  }
) {
  const params = await props.params;
  const projectResult = await getProjectDetail(params.projectId);
  if (!projectResult.ok) {
    if (projectResult.kind === "not_found") notFound();
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <RequestFailureCard failure={projectResult} />
      </div>
    );
  }
  const project = projectResult.data;
  const base = `/projects/${project.projectId}`;
  const [sheetsResult, summaryResult] = await Promise.all([
    getPlanSheets(project.projectId),
    getPlanSheetSummary(project.projectId),
  ]);
  if (!sheetsResult.ok) {
    if (sheetsResult.kind === "not_found") notFound();
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <RequestFailureCard failure={sheetsResult} />
      </div>
    );
  }
  const sheets = sheetsResult.data;
  const summary = summaryResult.ok ? summaryResult.data : null;

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Plan sheets"
        description="Project plan sheet index. Open a sheet to see its review-support metadata, hotspots, CAD metadata, and plan references. Nothing here is a finding about the sheet content."
      />

      <div className="mx-auto max-w-6xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/plan-consistency`} className="nav-link">
            Plan consistency
          </Link>
          <Link href={`${base}/cad`} className="nav-link">
            CAD intake
          </Link>
        </div>

        <BoundaryNote note={SHEETS_BOUNDARY_NOTE} />

        {summary ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <MetricCard value={summary.totalSheets} label="Total sheets" />
            <MetricCard value={summary.presentSheets} label="Present sheets" />
            <MetricCard
              value={summary.missingOrReferencedNotIncluded}
              label="Missing / referenced"
              accent={
                summary.missingOrReferencedNotIncluded > 0 ? "amber" : "slate"
              }
            />
            <MetricCard
              value={summary.sheetsWithRelatedFindings}
              label="Sheets with findings"
            />
            <MetricCard
              value={summary.cadMetadataRecords}
              label="CAD metadata records"
            />
          </div>
        ) : null}

        {sheets.length === 0 ? (
          <EmptyState
            title="No plan sheets available"
            description="No plan sheet records are available for this project, or the backend is unavailable. This is a workflow or connection state, not a finding about the plan set."
          />
        ) : (
          <SectionCard title={`Plan sheets (${sheets.length})`}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-2 pr-4">Sheet</th>
                    <th className="py-2 pr-4">Title</th>
                    <th className="py-2 pr-4">Discipline</th>
                    <th className="py-2 pr-4">Revision</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4">Links</th>
                  </tr>
                </thead>
                <tbody>
                  {sheets.map((sheet) => (
                    <tr
                      key={sheet.sheetId}
                      className="border-b border-slate-100 align-top"
                    >
                      <td className="py-2 pr-4 font-medium">
                        <Link
                          href={`${base}/plan-sheets/${sheet.sheetId}`}
                          className="text-water-700 hover:underline"
                        >
                          {sheet.sheetNumber || sheet.sheetId}
                        </Link>
                      </td>
                      <td className="py-2 pr-4 text-slate-700">
                        {sheet.sheetTitle}
                      </td>
                      <td className="py-2 pr-4 text-slate-600">
                        {sheet.discipline}
                      </td>
                      <td className="py-2 pr-4 text-slate-600">
                        {sheet.revision}
                      </td>
                      <td className="py-2 pr-4">
                        <StatusChip label={humanizeStatus(sheet.status)} />
                      </td>
                      <td className="py-2 pr-4 text-xs text-slate-500">
                        {sheet.relatedDocuments.length} docs,{" "}
                        {sheet.relatedChecklistItems.length} checklist,{" "}
                        {sheet.relatedFindings.length} findings
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        )}
      </div>
    </div>
  );
}
