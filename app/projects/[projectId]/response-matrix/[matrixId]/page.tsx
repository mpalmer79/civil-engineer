import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import AddMatrixItemsToPackagePanel from "@/components/AddMatrixItemsToPackagePanel";
import {
  getResponseMatrix,
  listResponseMatrixItems,
  listResponsePackages,
} from "@/lib/api";

export const dynamic = "force-dynamic";

// Response matrix detail page. Shows the matrix status summary and the table of
// review-support items with their applicant response, reviewer follow-up, and
// carry-forward status. Statuses are review-support labels only. Nothing here
// approves, certifies, verifies, resolves, or closes anything.
export default async function ResponseMatrixDetailPage({
  params,
}: {
  params: { projectId: string; matrixId: string };
}) {
  const [matrix, items, packages] = await Promise.all([
    getResponseMatrix(params.projectId, params.matrixId),
    listResponseMatrixItems(params.projectId, params.matrixId),
    listResponsePackages(params.projectId),
  ]);
  if (!matrix) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;

  const summaryRow = (label: string, summary: Record<string, number>) => {
    const entries = Object.entries(summary);
    return (
      <div className="flex flex-col gap-1 border-b border-slate-100 py-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {label}
        </span>
        {entries.length === 0 ? (
          <span className="text-sm text-slate-500">No items yet</span>
        ) : (
          <div className="flex flex-wrap gap-2">
            {entries.map(([status, count]) => (
              <span
                key={status}
                className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200"
              >
                {status}: {count}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      <PageHeader
        eyebrow="Response matrix"
        title={matrix.name}
        description="Review-support items organized for applicant response tracking. Applicant responses are recorded for reviewer review, never as proof. Carry-forward keeps an item under review across rounds."
      />

      <div className="mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`${base}/response-matrix`} className="nav-link">
            Back to response matrices
          </Link>
          <Link href={`${base}/resubmittals`} className="nav-link">
            Resubmittal rounds
          </Link>
          <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
            Status: {matrix.status}
          </span>
          <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
            Round: {matrix.currentRoundNumber}
          </span>
          <SourceBadge sourceMode={matrix.sourceMode} />
        </div>

        <SectionCard title="Status summary">
          {summaryRow("Applicant response", matrix.applicantResponseSummary)}
          {summaryRow("Reviewer follow-up", matrix.reviewerFollowUpSummary)}
          {summaryRow("Carry-forward", matrix.carryForwardSummary)}
        </SectionCard>

        <SectionCard
          title="Matrix items"
          description="Each item links back to a reviewer finding or checklist review item. Open an item to record an applicant response or carry it forward."
        >
          {items === null ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              Matrix items are served by the backend. Start the API to view them.
            </p>
          ) : items.length === 0 ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              No items in this matrix yet. Add reviewer findings or checklist
              review items from their detail pages.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[40rem] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-2 pr-4">Item</th>
                    <th className="py-2 pr-4">Category</th>
                    <th className="py-2 pr-4">Applicant response</th>
                    <th className="py-2 pr-4">Reviewer follow-up</th>
                    <th className="py-2 pr-4">Carry-forward</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr
                      key={item.responseMatrixItemId}
                      className="border-b border-slate-100"
                    >
                      <td className="py-2 pr-4">
                        <Link
                          href={`${base}/response-matrix/items/${item.responseMatrixItemId}`}
                          className="font-semibold text-water-700 hover:underline"
                        >
                          {item.itemNumber ?? "Item"}
                        </Link>
                      </td>
                      <td className="py-2 pr-4 text-slate-700">
                        {item.category}
                      </td>
                      <td className="py-2 pr-4 text-slate-600">
                        {item.applicantResponseStatus}
                      </td>
                      <td className="py-2 pr-4 text-slate-600">
                        {item.reviewerFollowUpStatus}
                      </td>
                      <td className="py-2 pr-4 text-slate-600">
                        {item.carryForwardStatus}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>

        {packages !== null && items !== null ? (
          <AddMatrixItemsToPackagePanel
            projectId={params.projectId}
            matrixItemIds={items.map((i) => i.responseMatrixItemId)}
            packages={packages}
          />
        ) : null}

        <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          This matrix is review-support only. Status labels describe reviewer
          workflow state, not a final engineering decision. Every item needs
          human review.
        </p>
      </div>
    </div>
  );
}
