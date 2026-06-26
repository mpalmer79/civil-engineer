import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MatrixItemActions from "@/components/MatrixItemActions";
import AddToResponsePackageButton from "@/components/AddToResponsePackageButton";
import { getResponseMatrixItem, listResponsePackages } from "@/lib/api";

export const dynamic = "force-dynamic";

// Response matrix item detail page. Shows the reviewer comment draft, the source
// finding or checklist item, the recorded applicant response, and reviewer
// actions. Applicant responses are recorded for reviewer review, never as proof.
// Carry-forward keeps the item under review across rounds. Nothing here approves,
// certifies, verifies, resolves, or closes anything.
export default async function ResponseMatrixItemDetailPage({
  params,
}: {
  params: { projectId: string; itemId: string };
}) {
  const [item, packages] = await Promise.all([
    getResponseMatrixItem(params.projectId, params.itemId),
    listResponsePackages(params.projectId),
  ]);
  if (!item) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;

  const metadata: [string, string | null][] = [
    ["Item number", item.itemNumber],
    ["Category", item.category],
    ["Applicant response status", item.applicantResponseStatus],
    ["Reviewer follow-up status", item.reviewerFollowUpStatus],
    ["Carry-forward status", item.carryForwardStatus],
    ["Current review round", String(item.currentRoundNumber)],
    ["Carried from round", item.carriedFromRoundNumber
      ? String(item.carriedFromRoundNumber)
      : null],
    ["Carried to round", item.carriedToRoundNumber
      ? String(item.carriedToRoundNumber)
      : null],
    ["Created by", item.createdByName ?? "Seeded demo"],
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Response matrix item"
        title={item.itemNumber ? `Item ${item.itemNumber}` : "Matrix item"}
        description="A single review-support item tracked for applicant response. Recording an applicant response stores it for reviewer review. It does not finalize a review outcome."
      />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`${base}/response-matrix/${item.responseMatrixId}`}
            className="nav-link"
          >
            Back to response matrix
          </Link>
          {item.sourceFindingId ? (
            <Link
              href={`${base}/findings/${item.sourceFindingId}`}
              className="nav-link"
            >
              Source finding
            </Link>
          ) : null}
        </div>

        <SectionCard title="Item metadata">
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
          {item.reviewerCommentDraft ? (
            <p className="mt-3 text-sm text-slate-700">
              <span className="font-semibold text-slate-500">
                Reviewer comment draft:
              </span>{" "}
              {item.reviewerCommentDraft}
            </p>
          ) : null}
          {item.requestedEvidence ? (
            <p className="mt-2 text-sm text-slate-700">
              <span className="font-semibold text-slate-500">
                Requested evidence:
              </span>{" "}
              {item.requestedEvidence}
            </p>
          ) : null}
          {item.applicantResponseText ? (
            <p className="mt-2 text-sm text-slate-700">
              <span className="font-semibold text-slate-500">
                Recorded applicant response:
              </span>{" "}
              {item.applicantResponseText}
            </p>
          ) : null}
          {item.reviewerNote ? (
            <p className="mt-2 text-sm text-slate-700">
              <span className="font-semibold text-slate-500">
                Reviewer note:
              </span>{" "}
              {item.reviewerNote}
            </p>
          ) : null}
        </SectionCard>

        <MatrixItemActions projectId={params.projectId} item={item} />

        {packages !== null ? (
          <AddToResponsePackageButton
            projectId={params.projectId}
            sourceType="matrix-item"
            sourceId={item.responseMatrixItemId}
            packages={packages}
          />
        ) : null}

        <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          This item is review-support only. The recorded applicant response is
          stored for reviewer review, never as proof and never as a final
          outcome. Carry-forward means continued review, not resolution.
        </p>
      </div>
    </div>
  );
}
