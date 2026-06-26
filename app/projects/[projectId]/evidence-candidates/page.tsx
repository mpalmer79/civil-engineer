import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import {
  getProjectDetail,
  listProjectDocuments,
  listProjectEvidenceCandidates,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function EvidenceCandidateQueuePage({
  params,
}: {
  params: { projectId: string };
}) {
  const [project, candidates, documents] = await Promise.all([
    getProjectDetail(params.projectId),
    listProjectEvidenceCandidates(params.projectId),
    listProjectDocuments(params.projectId),
  ]);
  if (!project) {
    notFound();
  }
  const base = `/projects/${project.projectId}`;
  const documentName = (id: string) => {
    const d = documents?.find((doc) => doc.documentId === id);
    return d?.originalFileName ?? d?.fileName ?? id;
  };

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Evidence candidate queue"
        description="Saved retrieval candidates for reviewer triage. Each candidate requires reviewer confirmation. Promote a candidate into a reviewer draft finding or dismiss it. Nothing here finalizes a review outcome."
      />

      <div className="mx-auto max-w-6xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/evidence-search`} className="nav-link">
            Evidence search
          </Link>
        </div>

        {candidates === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Evidence candidates are served by the backend. Start the API to
              view them.
            </p>
          </SectionCard>
        ) : candidates.length === 0 ? (
          <SectionCard title="No candidates yet">
            <p className="text-sm text-slate-600">
              No evidence candidates saved yet. Use{" "}
              <Link
                href={`${base}/evidence-search`}
                className="text-water-700 hover:underline"
              >
                Evidence search
              </Link>{" "}
              to find indexed page text and save candidates for reviewer triage.
            </p>
          </SectionCard>
        ) : (
          <ul className="space-y-3">
            {candidates.map((c) => (
              <li key={c.evidenceCandidateId} className="surface-card p-4 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Link
                    href={`${base}/evidence-candidates/${c.evidenceCandidateId}`}
                    className="font-semibold text-water-700 hover:underline"
                  >
                    {c.candidateTitle}
                  </Link>
                  <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                    {c.candidateStatus}
                  </span>
                </div>
                <p className="mt-1 text-slate-600">
                  {documentName(c.documentId)}
                  {c.pageNumber ? `, page ${c.pageNumber}` : ""}
                </p>
                {c.candidateExcerpt ? (
                  <p className="mt-1 italic text-slate-600">
                    &ldquo;{c.candidateExcerpt}&rdquo;
                  </p>
                ) : null}
                {c.matchTerms.length > 0 ? (
                  <p className="mt-1 text-xs text-slate-500">
                    Match terms: {c.matchTerms.join(", ")}
                  </p>
                ) : null}
                {c.checklistItemId ? (
                  <p className="mt-1 text-xs text-slate-500">
                    Linked checklist item: {c.checklistItemId}
                  </p>
                ) : null}
                {c.reviewerNote ? (
                  <p className="mt-1 text-xs text-slate-500">
                    Reviewer note: {c.reviewerNote}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
