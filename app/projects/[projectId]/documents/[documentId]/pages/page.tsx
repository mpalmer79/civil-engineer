import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
import { listDocumentPages } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DocumentPagesPage({
  params,
}: {
  params: { projectId: string; documentId: string };
}) {
  const pages = await listDocumentPages(params.projectId, params.documentId);
  const base = `/projects/${params.projectId}/documents/${params.documentId}`;

  return (
    <div>
      <PageHeader
        eyebrow="Document pages"
        title="Indexed page records"
        description="Page-level review records produced by indexing the uploaded PDF. Each page records its text extraction status, character and word counts, and any extraction warnings. This is review-support evidence, not an engineering conclusion."
      />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <Link href={base} className="nav-link">
          Back to document
        </Link>

        {pages === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Page records are served by the backend. Start the API to view
              indexed pages.
            </p>
          </SectionCard>
        ) : pages.length === 0 ? (
          <EmptyState
            title="No pages indexed yet"
            description="This document has not been indexed yet. Index the PDF from the document detail page to create page records."
          />
        ) : (
          <ul className="list-container">
            {pages.map((p) => (
              <li
                key={p.documentPageId}
                className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold text-slate-800">
                    Page {p.pageNumber}
                  </span>
                  <StatusChip label={p.textExtractionStatus} prefix="text" />
                  <StatusChip label={`${p.charCount} chars`} />
                  <StatusChip label={`${p.wordCount} words`} />
                  {p.extractionWarnings.length > 0 ? (
                    <StatusChip
                      label={`${p.extractionWarnings.length} warning${
                        p.extractionWarnings.length === 1 ? "" : "s"
                      }`}
                      tone="warning"
                    />
                  ) : null}
                </div>
                <Link
                  href={`${base}/pages/${p.pageNumber}`}
                  className="btn btn-secondary btn-sm shrink-0"
                >
                  View page
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
