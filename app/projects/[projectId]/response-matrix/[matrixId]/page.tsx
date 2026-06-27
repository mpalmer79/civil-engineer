import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
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
              <StatusChip key={status} label={String(count)} prefix={status} />
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
          <StatusChip label={matrix.status} prefix="status" />
          <StatusChip
            label={String(matrix.currentRoundNumber)}
            prefix="round"
          />
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
            <p className="alert alert-warning">
              Matrix items are served by the backend. Start the API to view them.
            </p>
          ) : items.length === 0 ? (
            <EmptyState
              title="No items in this matrix yet"
              description="Add reviewer findings or checklist review items from their detail pages."
            />
          ) : (
            <ul className="list-container">
              {items.map((item) => (
                <li
                  key={item.responseMatrixItemId}
                  className="flex flex-col gap-3 px-4 py-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Link
                      href={`${base}/response-matrix/items/${item.responseMatrixItemId}`}
                      className="font-semibold text-water-700 hover:underline"
                    >
                      {item.itemNumber ?? "Item"}
                    </Link>
                    <span className="text-xs text-slate-500">{item.category}</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <StatusChip
                      label={item.applicantResponseStatus}
                      prefix="applicant"
                    />
                    <StatusChip
                      label={item.reviewerFollowUpStatus}
                      prefix="follow-up"
                    />
                    <StatusChip
                      label={item.carryForwardStatus}
                      prefix="carry-forward"
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        {packages !== null && items !== null ? (
          <AddMatrixItemsToPackagePanel
            projectId={params.projectId}
            matrixItemIds={items.map((i) => i.responseMatrixItemId)}
            packages={packages}
          />
        ) : null}

        <p className="alert alert-info">
          This matrix is review-support only. Status labels describe reviewer
          workflow state, not a final engineering decision. Every item needs
          human review.
        </p>
      </div>
    </div>
  );
}
