import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
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
          <SectionCard title="No pages indexed yet">
            <p className="text-sm text-slate-600">
              This document has not been indexed yet. Index the PDF from the
              document detail page to create page records.
            </p>
          </SectionCard>
        ) : (
          <SectionCard>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">Page</th>
                    <th className="px-3 py-2">Text extraction</th>
                    <th className="px-3 py-2">Chars</th>
                    <th className="px-3 py-2">Words</th>
                    <th className="px-3 py-2">Warnings</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {pages.map((p) => (
                    <tr
                      key={p.documentPageId}
                      className="border-b border-slate-100"
                    >
                      <td className="px-3 py-2 font-medium text-slate-800">
                        {p.pageNumber}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {p.textExtractionStatus}
                      </td>
                      <td className="px-3 py-2 text-slate-600">{p.charCount}</td>
                      <td className="px-3 py-2 text-slate-600">{p.wordCount}</td>
                      <td className="px-3 py-2 text-slate-600">
                        {p.extractionWarnings.length}
                      </td>
                      <td className="px-3 py-2">
                        <Link
                          href={`${base}/pages/${p.pageNumber}`}
                          className="text-water-700 hover:underline"
                        >
                          View page
                        </Link>
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
