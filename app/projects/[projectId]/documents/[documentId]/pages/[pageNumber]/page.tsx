import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import EvidenceCitationForm from "@/components/EvidenceCitationForm";
import { getDocumentPage } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DocumentPageDetail({
  params,
}: {
  params: { projectId: string; documentId: string; pageNumber: string };
}) {
  const pageNumber = Number(params.pageNumber);
  const page = await getDocumentPage(
    params.projectId,
    params.documentId,
    pageNumber,
  );
  if (!page) {
    notFound();
  }
  const base = `/projects/${params.projectId}/documents/${params.documentId}`;
  const hasText =
    page.textExtractionStatus === "text_extracted" && !!page.extractedText;

  return (
    <div>
      <PageHeader
        eyebrow={`Page ${page.pageNumber}`}
        title={page.pageLabel ?? `Page ${page.pageNumber}`}
        description="Indexed page record with extracted text where available. Extracted text is review-support evidence, not an engineering conclusion. Cite this page as evidence for a finding below."
      />

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`${base}/pages`} className="nav-link">
            Back to pages
          </Link>
          <Link
            href={`/projects/${params.projectId}/evidence-search`}
            className="nav-link"
          >
            Search similar evidence
          </Link>
          <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
            {page.textExtractionStatus}
          </span>
          <span className="text-sm text-slate-500">
            {page.charCount} chars, {page.wordCount} words
          </span>
        </div>

        {page.extractionWarnings.length > 0 ? (
          <SectionCard title="Extraction warnings">
            <ul className="list-disc pl-5 text-sm text-amber-700">
              {page.extractionWarnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </SectionCard>
        ) : null}

        <SectionCard title="Extracted text">
          {hasText ? (
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-sm text-slate-800">
              {page.extractedText}
            </pre>
          ) : (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
              No extractable text on this page. The page may be a scanned image.
              OCR is not available in this sprint. A reviewer can still create a
              page-level reference citation below.
            </p>
          )}
        </SectionCard>

        <EvidenceCitationForm
          projectId={params.projectId}
          documentId={params.documentId}
          pageNumber={page.pageNumber}
          defaultExcerpt={hasText ? undefined : ""}
        />
      </div>
    </div>
  );
}
