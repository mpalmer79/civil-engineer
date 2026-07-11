import Link from "next/link";
import RequestFailureCard from "@/components/RequestFailureCard";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import {
  getProjectChecklist,
  listProjectChecklistItems,
} from "@/lib/api";

export const dynamic = "force-dynamic";

const EVIDENCE_STATUS_LABELS: Record<string, string> = {
  not_reviewed: "Not reviewed",
  evidence_found: "Evidence found",
  missing_evidence: "Missing evidence",
  conflicting_evidence: "Conflicting evidence",
  unclear_evidence: "Unclear evidence",
  extraction_unavailable: "Extraction unavailable",
  needs_reviewer_confirmation: "Needs reviewer confirmation",
};

export default async function ChecklistDetailPage(
  props: {
    params: Promise<{ projectId: string; checklistId: string }>;
  }
) {
  const params = await props.params;
  const [checklistResult, itemsResult] = await Promise.all([
    getProjectChecklist(params.projectId, params.checklistId),
    listProjectChecklistItems(params.projectId, params.checklistId),
  ]);
  if (!checklistResult.ok) {
    if (checklistResult.kind === "not_found") notFound();
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <RequestFailureCard failure={checklistResult} />
      </div>
    );
  }
  const checklist = checklistResult.data;
  const items = itemsResult.ok ? itemsResult.data : null;
  const base = `/projects/${params.projectId}`;
  const checklistBase = `${base}/checklists/${params.checklistId}`;
  const itemList = items ?? [];
  const categories = Array.from(new Set(itemList.map((i) => i.category)));

  return (
    <div>
      <PageHeader
        eyebrow={checklist.name}
        title="Checklist review"
        description="Checklist evidence status is for review support and requires human confirmation. It does not approve plans, certify compliance, or validate design."
      />

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`${base}/checklists`} className="nav-link">
            Back to checklists
          </Link>
          <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
            {checklist.status}
          </span>
          <span className="text-sm text-slate-500">
            {checklist.itemCount} item(s)
          </span>
        </div>

        {categories.map((category) => (
          <SectionCard key={category} title={category}>
            <ul className="space-y-2">
              {itemList
                .filter((i) => i.category === category)
                .map((item) => (
                  <li
                    key={item.projectChecklistItemId}
                    className="rounded-lg border border-slate-200 p-3 text-sm"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <Link
                        href={`${checklistBase}/items/${item.projectChecklistItemId}`}
                        className="font-semibold text-water-700 hover:underline"
                      >
                        {item.itemCode}: {item.requirementText}
                      </Link>
                      <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                        {EVIDENCE_STATUS_LABELS[item.evidenceStatus] ??
                          item.evidenceStatus}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      Applicability: {item.applicabilityStatus} · Review:{" "}
                      {item.reviewStatus} · Risk: {item.riskLevel}
                    </p>
                    <p className="mt-1 text-slate-600">
                      <span className="font-semibold text-slate-500">
                        Expected evidence:
                      </span>{" "}
                      {item.expectedEvidence}
                    </p>
                    {item.reviewerNote ? (
                      <p className="mt-1 text-xs text-slate-500">
                        Reviewer note: {item.reviewerNote}
                      </p>
                    ) : null}
                  </li>
                ))}
            </ul>
          </SectionCard>
        ))}
      </div>
    </div>
  );
}
