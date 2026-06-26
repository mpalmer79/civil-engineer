import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import { getProjectDetail, listProjectDocuments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectDocumentsPage({
  params,
}: {
  params: { projectId: string };
}) {
  const [project, documents] = await Promise.all([
    getProjectDetail(params.projectId),
    listProjectDocuments(params.projectId),
  ]);
  if (!project) {
    notFound();
  }
  const base = `/projects/${project.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Documents"
        description="Demo documents appear for Brookside Meadows. User-registered and user-uploaded documents appear for real project records. A processing status tracks intake handling only and does not imply approval."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between gap-4">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link
            href={`${base}/documents/register`}
            className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700"
          >
            Register document
          </Link>
        </div>

        {documents === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Documents are served by the backend. Start the API to view and
              register documents.
            </p>
          </SectionCard>
        ) : documents.length === 0 ? (
          <SectionCard title="No documents yet">
            <p className="text-sm text-slate-600">
              No documents have been registered or uploaded for this project
              record yet.
            </p>
          </SectionCard>
        ) : (
          <SectionCard>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">Document</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Processing</th>
                    <th className="px-3 py-2">Revision</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((d) => (
                    <tr key={d.documentId} className="border-b border-slate-100">
                      <td className="px-3 py-2 font-medium text-slate-800">
                        {d.originalFileName ?? d.fileName}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {d.documentType}
                      </td>
                      <td className="px-3 py-2">
                        <SourceBadge sourceMode={d.sourceMode} />
                      </td>
                      <td className="px-3 py-2 text-slate-600">{d.status}</td>
                      <td className="px-3 py-2 text-slate-600">
                        {d.processingStatus ?? "n/a"}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {d.revisionLabel ?? "n/a"}
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
