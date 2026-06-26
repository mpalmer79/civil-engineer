import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import EvidenceSearchClient from "@/components/EvidenceSearchClient";
import { getProjectDetail, listProjectDocuments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function EvidenceSearchPage({
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
  const docs = (documents ?? []).map((d) => ({
    documentId: d.documentId,
    label: d.originalFileName ?? d.fileName,
    documentType: d.documentType,
  }));
  const documentTypes = Array.from(
    new Set((documents ?? []).map((d) => d.documentType)),
  ).sort();
  const hasIndexedDocuments = (documents ?? []).some(
    (d) => d.textExtractionStatus === "text_extracted",
  );

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Evidence search"
        description="Search indexed PDF page text for this project. Retrieval is deterministic and local. There are no live AI calls. Every result is an evidence candidate that requires reviewer confirmation, not a conclusion."
      />

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/evidence-candidates`} className="nav-link">
            Candidate queue
          </Link>
          <Link href={`${base}/checklists`} className="nav-link">
            Project checklists
          </Link>
          <Link href={`${base}/documents`} className="nav-link">
            Documents
          </Link>
        </div>

        {!hasIndexedDocuments ? (
          <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            No indexed page text is available yet. Upload and index a digital
            PDF before searching evidence.
          </p>
        ) : null}

        <EvidenceSearchClient
          projectId={project.projectId}
          documents={docs}
          documentTypes={documentTypes}
        />
      </div>
    </div>
  );
}
