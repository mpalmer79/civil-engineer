import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import ChecklistItemReviewPanel from "@/components/ChecklistItemReviewPanel";
import { listProjectChecklistItems } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ChecklistItemDetailPage({
  params,
}: {
  params: { projectId: string; checklistId: string; itemId: string };
}) {
  const items = await listProjectChecklistItems(
    params.projectId,
    params.checklistId,
  );
  const item = items?.find((i) => i.projectChecklistItemId === params.itemId);
  if (!item) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;
  const checklistBase = `${base}/checklists/${params.checklistId}`;

  const metadata: [string, string | null][] = [
    ["Item code", item.itemCode],
    ["Category", item.category],
    ["Risk level", item.riskLevel],
    ["Applicability status", item.applicabilityStatus],
    ["Evidence status", item.evidenceStatus],
    ["Review status", item.reviewStatus],
    ["Related draft finding", item.relatedFindingId ?? "none"],
  ];

  return (
    <div>
      <PageHeader
        eyebrow={`${item.itemCode} · ${item.category}`}
        title={item.requirementText}
        description="Checklist evidence status is for review support and requires human confirmation. It does not approve plans, certify compliance, or validate design."
      />

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={checklistBase} className="nav-link">
            Back to checklist
          </Link>
          {item.relatedFindingId ? (
            <Link
              href={`${base}/findings/${item.relatedFindingId}`}
              className="nav-link"
            >
              View draft finding
            </Link>
          ) : null}
        </div>

        <SectionCard title="Requirement detail">
          <p className="text-sm text-slate-700">
            <span className="font-semibold text-slate-500">
              Expected evidence:
            </span>{" "}
            {item.expectedEvidence}
          </p>
          <dl className="mt-4 grid gap-x-6 gap-y-3 sm:grid-cols-2">
            {metadata.map(([label, value]) => (
              <div
                key={label}
                className="flex justify-between gap-4 border-b border-slate-100 pb-2"
              >
                <dt className="text-sm font-semibold text-slate-500">{label}</dt>
                <dd className="text-sm text-slate-800">{value}</dd>
              </div>
            ))}
          </dl>
          {item.reviewerNote ? (
            <p className="mt-3 text-sm text-slate-700">
              <span className="font-semibold text-slate-500">
                Reviewer note:
              </span>{" "}
              {item.reviewerNote}
            </p>
          ) : null}
        </SectionCard>

        <ChecklistItemReviewPanel projectId={params.projectId} item={item} />
      </div>
    </div>
  );
}
