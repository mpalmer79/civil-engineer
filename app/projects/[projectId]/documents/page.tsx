import Link from "next/link";
import RequestFailureCard from "@/components/RequestFailureCard";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
import { getProjectDetail, listProjectDocuments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectDocumentsPage(
  props: {
    params: Promise<{ projectId: string }>;
  }
) {
  const params = await props.params;
  const [projectResult, documentsResult] = await Promise.all([
    getProjectDetail(params.projectId),
    listProjectDocuments(params.projectId),
  ]);
  if (!projectResult.ok) {
    if (projectResult.kind === "not_found") notFound();
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <RequestFailureCard failure={projectResult} />
      </div>
    );
  }
  const project = projectResult.data;
  const documents = documentsResult.ok ? documentsResult.data : null;
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
            className="btn btn-primary btn-sm"
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
          <EmptyState
            title="No documents yet"
            description="No documents have been registered or uploaded for this project record yet."
            action={
              <Link
                href={`${base}/documents/register`}
                className="btn btn-primary btn-sm"
              >
                Register document
              </Link>
            }
          />
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2">
            {documents.map((d) => (
              <li key={d.documentId} className="surface-card p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <Link
                    href={`${base}/documents/${d.documentId}`}
                    className="break-words text-sm font-semibold text-water-700 hover:underline"
                  >
                    {d.originalFileName ?? d.fileName}
                  </Link>
                  <SourceBadge sourceMode={d.sourceMode} />
                </div>
                <p className="mt-1 text-xs text-slate-500">{d.documentType}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <StatusChip
                    label={d.processingStatus ?? "n/a"}
                    prefix="Processing"
                  />
                  <StatusChip
                    label={d.storageProvider ?? "n/a"}
                    prefix="Storage"
                  />
                  {d.storageProvider ? (
                    <StatusChip
                      label={d.fileAvailable ? "file available" : "file unavailable"}
                      tone={d.fileAvailable ? "success" : "warning"}
                    />
                  ) : (
                    <StatusChip label="n/a" prefix="File" />
                  )}
                  <StatusChip
                    label={d.pageCount != null ? String(d.pageCount) : "n/a"}
                    prefix="Pages"
                  />
                  <StatusChip
                    label={d.textExtractionStatus ?? "not indexed"}
                    prefix="Text extraction"
                  />
                  <StatusChip
                    label={d.indexedAt ? "indexed" : "not indexed"}
                    tone={d.indexedAt ? "brand" : "neutral"}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
