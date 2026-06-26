import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import {
  getProjectDetail,
  listProjectDocuments,
  listProjectEvidenceCitations,
  listProjectFindings,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectEvidenceCitationsPage({
  params,
}: {
  params: { projectId: string };
}) {
  const [project, citations, findings, documents] = await Promise.all([
    getProjectDetail(params.projectId),
    listProjectEvidenceCitations(params.projectId),
    listProjectFindings(params.projectId),
    listProjectDocuments(params.projectId),
  ]);
  if (!project) {
    notFound();
  }
  const base = `/projects/${project.projectId}`;
  const findingTitle = (id: string) =>
    findings?.find((f) => f.findingId === id)?.title ?? id;
  const documentName = (id: string) => {
    const d = documents?.find((doc) => doc.documentId === id);
    return d?.originalFileName ?? d?.fileName ?? id;
  };

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Evidence citations"
        description="Reviewer-selected, page-level evidence citations across this project. Each citation is a source reference requiring reviewer confirmation, not proof of correctness and not an engineering conclusion."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <Link href={base} className="nav-link">
          Back to project
        </Link>

        {citations === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Evidence citations are served by the backend. Start the API to view
              them.
            </p>
          </SectionCard>
        ) : citations.length === 0 ? (
          <SectionCard title="No citations yet">
            <p className="text-sm text-slate-600">
              No evidence citations exist for this project yet. Index a document
              PDF and cite a page from a finding.
            </p>
          </SectionCard>
        ) : (
          <SectionCard>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">Finding</th>
                    <th className="px-3 py-2">Document</th>
                    <th className="px-3 py-2">Page</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Reviewer note</th>
                    <th className="px-3 py-2">Created by</th>
                  </tr>
                </thead>
                <tbody>
                  {citations.map((c) => (
                    <tr
                      key={c.evidenceCitationId}
                      className="border-b border-slate-100 align-top"
                    >
                      <td className="px-3 py-2">
                        <Link
                          href={`${base}/findings/${c.findingId}`}
                          className="text-water-700 hover:underline"
                        >
                          {findingTitle(c.findingId)}
                        </Link>
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {documentName(c.documentId)}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {c.pageNumber ?? "n/a"}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {c.citationStatus}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {c.citationType}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {c.reviewerNote ?? ""}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {c.createdByName ?? "n/a"}
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
