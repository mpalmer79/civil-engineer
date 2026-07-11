import Link from "next/link";
import RequestFailureCard from "@/components/RequestFailureCard";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import CandidateActions from "@/components/CandidateActions";
import PromoteCandidateForm from "@/components/PromoteCandidateForm";
import {
  getEvidenceCandidate,
  listProjectDocuments,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function EvidenceCandidateDetailPage(
  props: {
    params: Promise<{ projectId: string; candidateId: string }>;
  }
) {
  const params = await props.params;
  const [candidateResult, documentsResult] = await Promise.all([
    getEvidenceCandidate(params.projectId, params.candidateId),
    listProjectDocuments(params.projectId),
  ]);
  if (!candidateResult.ok) {
    if (candidateResult.kind === "not_found") notFound();
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <RequestFailureCard failure={candidateResult} />
      </div>
    );
  }
  const candidate = candidateResult.data;
  const documents = documentsResult.ok ? documentsResult.data : null;
  const base = `/projects/${params.projectId}`;
  const document = documents?.find(
    (d) => d.documentId === candidate.documentId,
  );
  const documentName =
    document?.originalFileName ?? document?.fileName ?? candidate.documentId;

  const metadata: [string, string | null][] = [
    ["Status", candidate.candidateStatus],
    ["Origin", candidate.candidateOrigin],
    ["Document", documentName],
    ["Page", candidate.pageNumber ? String(candidate.pageNumber) : "n/a"],
    ["Relevance score", candidate.rankingScore.toFixed(2)],
    ["Linked finding", candidate.findingId ?? "none"],
    ["Linked checklist item", candidate.checklistItemId ?? "none"],
    ["Created by", candidate.createdByName ?? "Demo Reviewer"],
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Evidence candidate"
        title={candidate.candidateTitle}
        description="A reviewer-controlled retrieval candidate. It requires reviewer confirmation and is not a conclusion. Promote it into a reviewer draft finding or dismiss it."
      />

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={`${base}/evidence-candidates`} className="nav-link">
            Back to candidate queue
          </Link>
          <Link href={`${base}/evidence-search`} className="nav-link">
            Evidence search
          </Link>
        </div>

        <SectionCard title="Candidate detail">
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
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
          {candidate.candidateExcerpt ? (
            <p className="mt-3 italic text-sm text-slate-600">
              &ldquo;{candidate.candidateExcerpt}&rdquo;
            </p>
          ) : null}
          {candidate.matchTerms.length > 0 ? (
            <p className="mt-2 text-xs text-slate-500">
              Match terms: {candidate.matchTerms.join(", ")}
            </p>
          ) : null}
          {candidate.rankingReason ? (
            <p className="mt-1 text-xs text-slate-500">
              {candidate.rankingReason}
            </p>
          ) : null}
        </SectionCard>

        <CandidateActions
          projectId={params.projectId}
          candidateId={candidate.evidenceCandidateId}
          defaultNote={candidate.reviewerNote}
          status={candidate.candidateStatus}
        />

        <PromoteCandidateForm
          projectId={params.projectId}
          candidateId={candidate.evidenceCandidateId}
          defaultTitle={candidate.candidateTitle}
          defaultExcerpt={candidate.candidateExcerpt}
          alreadyPromoted={candidate.candidateStatus === "promoted_to_draft"}
          promotedFindingId={candidate.promotedFindingId}
        />
      </div>
    </div>
  );
}
