import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import {
  getProjectFinding,
  listFindingCitations,
  listProjectEvidenceCandidates,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function FindingDetailPage({
  params,
}: {
  params: { projectId: string; findingId: string };
}) {
  const [finding, citations, candidates] = await Promise.all([
    getProjectFinding(params.projectId, params.findingId),
    listFindingCitations(params.projectId, params.findingId),
    listProjectEvidenceCandidates(params.projectId, {
      findingId: params.findingId,
    }),
  ]);
  if (!finding) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;

  const metadata: [string, string | null][] = [
    ["Category", finding.category],
    ["Risk level", finding.riskLevel],
    ["Evidence status", finding.evidenceStatus],
    ["Human review status", finding.humanReviewStatus],
    ["Origin", finding.findingOrigin],
    ["Created by", finding.createdByName ?? "Seeded demo"],
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Finding detail"
        title={finding.title}
        description="A review-support finding requiring human confirmation, with its reviewer-selected evidence citations. It does not approve, certify, verify, resolve, or close anything."
      />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`${base}/findings`} className="nav-link">
            Back to findings
          </Link>
          <Link href={`${base}/evidence-search`} className="nav-link">
            Search evidence for this finding
          </Link>
          <SourceBadge sourceMode={finding.sourceMode} />
        </div>

        <SectionCard title="Finding metadata">
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
          {finding.recommendedHumanAction ? (
            <p className="mt-3 text-sm text-slate-700">
              <span className="font-semibold text-slate-500">
                Recommended human action:
              </span>{" "}
              {finding.recommendedHumanAction}
            </p>
          ) : null}
          {finding.reviewerNotes ? (
            <p className="mt-2 text-sm text-slate-700">
              <span className="font-semibold text-slate-500">
                Reviewer notes:
              </span>{" "}
              {finding.reviewerNotes}
            </p>
          ) : null}
          {finding.relatedDocuments.length > 0 ? (
            <p className="mt-2 text-xs text-slate-500">
              Related documents: {finding.relatedDocuments.join(", ")}
            </p>
          ) : null}
          {finding.relatedChecklistItems.length > 0 ? (
            <p className="mt-2 text-xs text-slate-500">
              Related checklist item(s):{" "}
              {finding.relatedChecklistItems.join(", ")}
              {finding.findingOrigin === "checklist_review"
                ? " (created from checklist review)"
                : ""}
            </p>
          ) : null}
        </SectionCard>

        <SectionCard
          title="Evidence citations"
          description="Reviewer-selected, page-level evidence references. Add citations from an indexed document page."
        >
          <p className="mb-3 text-sm text-slate-600">
            To add a page-level citation, open a document, index its PDF, then
            cite a page.{" "}
            <Link href={`${base}/documents`} className="text-water-700 hover:underline">
              Go to documents
            </Link>
            . Use this finding ID:{" "}
            <code className="rounded bg-slate-100 px-1">{finding.findingId}</code>
          </p>
          {citations === null ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              Citations are served by the backend. Start the API to view them.
            </p>
          ) : citations.length === 0 ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              No evidence citations for this finding yet.
            </p>
          ) : (
            <ul className="space-y-2">
              {citations.map((c) => (
                <li
                  key={c.evidenceCitationId}
                  className="rounded-lg border border-slate-200 p-3 text-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-semibold text-slate-800">
                      {c.pageLabel ?? (c.pageNumber ? `Page ${c.pageNumber}` : "Document reference")}
                    </span>
                    <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                      {c.citationStatus}
                    </span>
                  </div>
                  {c.sectionLabel ? (
                    <p className="mt-1 text-slate-600">Section: {c.sectionLabel}</p>
                  ) : null}
                  {c.quotedExcerpt ? (
                    <p className="mt-1 italic text-slate-600">
                      &ldquo;{c.quotedExcerpt}&rdquo;
                    </p>
                  ) : null}
                  {c.reviewerNote ? (
                    <p className="mt-1 text-slate-600">{c.reviewerNote}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <SectionCard
          title="Retrieval candidates for this finding"
          description="Evidence candidates saved against this finding from deterministic retrieval. Each requires reviewer confirmation and is not a conclusion."
        >
          {candidates === null ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              Candidates are served by the backend. Start the API to view them.
            </p>
          ) : candidates.length === 0 ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              No retrieval candidates linked to this finding yet.
            </p>
          ) : (
            <ul className="space-y-2">
              {candidates.map((c) => (
                <li
                  key={c.evidenceCandidateId}
                  className="rounded-lg border border-slate-200 p-3 text-sm"
                >
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
                  {c.candidateExcerpt ? (
                    <p className="mt-1 italic text-slate-600">
                      &ldquo;{c.candidateExcerpt}&rdquo;
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
