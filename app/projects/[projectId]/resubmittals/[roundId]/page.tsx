import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
import {
  getResubmittalRound,
  getResubmittalRoundSummary,
} from "@/lib/api";

export const dynamic = "force-dynamic";

// Resubmittal round detail page. Shows the round metadata, the linked documents,
// the carried-forward items, and a review-support status summary. A resubmittal
// round records an applicant submission for reviewer review. It does not finalize
// a review outcome and does not resolve or close anything.
export default async function ResubmittalRoundDetailPage({
  params,
}: {
  params: { projectId: string; roundId: string };
}) {
  const [round, summary] = await Promise.all([
    getResubmittalRound(params.projectId, params.roundId),
    getResubmittalRoundSummary(params.projectId, params.roundId),
  ]);
  if (!round) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;

  const metadata: [string, string | null][] = [
    ["Round number", String(round.roundNumber)],
    ["Round label", round.roundLabel],
    ["Status", round.status],
    ["Received at", round.receivedAt],
    ["Submitted by", round.submittedByName],
    ["Submitted by organization", round.submittedByOrganization],
    ["Created by", round.createdByName ?? "Seeded demo"],
  ];

  const summaryRow = (label: string, data: Record<string, number>) => {
    const entries = Object.entries(data);
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
        eyebrow="Resubmittal round"
        title={`Round ${round.roundNumber}: ${round.roundLabel}`}
        description="A registered applicant resubmittal recorded for reviewer review. Linked documents and carried-forward items are organized for the reviewer. Nothing here finalizes a review outcome."
      />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`${base}/resubmittals`} className="nav-link">
            Back to resubmittal rounds
          </Link>
          <Link href={`${base}/response-matrix`} className="nav-link">
            Response matrix
          </Link>
        </div>

        <SectionCard title="Round metadata">
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            {metadata.map(([label, value]) => (
              <div
                key={label}
                className="flex justify-between gap-4 border-b border-slate-100 pb-2"
              >
                <dt className="text-sm font-semibold text-slate-500">{label}</dt>
                <dd className="text-sm text-slate-800">{value ?? "n/a"}</dd>
              </div>
            ))}
          </dl>
          {round.summary ? (
            <p className="mt-3 text-sm text-slate-700">
              <span className="font-semibold text-slate-500">Summary:</span>{" "}
              {round.summary}
            </p>
          ) : null}
        </SectionCard>

        <SectionCard
          title="Linked documents"
          description="Documents received with this resubmittal round, organized for reviewer review."
        >
          {round.documentIds.length === 0 ? (
            <EmptyState title="No documents linked to this round yet" />
          ) : (
            <ul className="list-container">
              {round.documentIds.map((docId) => (
                <li key={docId} className="px-4 py-3 text-sm">
                  <Link
                    href={`${base}/documents/${docId}`}
                    className="font-semibold text-water-700 hover:underline"
                  >
                    {docId}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <SectionCard
          title="Carried-forward items"
          description="Response matrix items carried into this round for continued reviewer review."
        >
          {round.carriedForwardItemIds.length === 0 ? (
            <EmptyState title="No items carried forward into this round yet" />
          ) : (
            <ul className="list-container">
              {round.carriedForwardItemIds.map((itemId) => (
                <li key={itemId} className="px-4 py-3 text-sm">
                  <Link
                    href={`${base}/response-matrix/items/${itemId}`}
                    className="font-semibold text-water-700 hover:underline"
                  >
                    {itemId}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        {summary ? (
          <SectionCard
            title="Status summary"
            description="Review-support status counts across the matrix items connected to this round."
          >
            <p className="mb-2 text-sm text-slate-600">
              {summary.matrixItemCount} matrix item(s) connected.
            </p>
            {summaryRow("Applicant response", summary.applicantResponseSummary)}
            {summaryRow("Carry-forward", summary.carryForwardSummary)}
          </SectionCard>
        ) : null}

        <p className="alert alert-info">
          This resubmittal round is review-support only. Status labels describe
          reviewer workflow state, not a final engineering decision. Every round
          needs human review.
        </p>
      </div>
    </div>
  );
}
