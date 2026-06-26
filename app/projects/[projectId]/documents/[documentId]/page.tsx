import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import IndexPdfButton from "@/components/IndexPdfButton";
import { getProjectDocument } from "@/lib/api";

export const dynamic = "force-dynamic";

function isPdf(name: string | null, contentType: string | null): boolean {
  if (name && name.toLowerCase().endsWith(".pdf")) return true;
  return (contentType ?? "").toLowerCase() === "application/pdf";
}

export default async function DocumentDetailPage({
  params,
}: {
  params: { projectId: string; documentId: string };
}) {
  const doc = await getProjectDocument(params.projectId, params.documentId);
  if (!doc) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;
  const hasFile = doc.sourceMode === "user_uploaded" && doc.uploadStatus === "stored";
  const pdf = isPdf(doc.originalFileName ?? doc.fileName, doc.contentType);
  const canIndex = hasFile && pdf;
  const disabledReason = !hasFile
    ? "PDF indexing requires an uploaded PDF file. This document has no stored file."
    : !pdf
      ? "PDF indexing requires a PDF document. This document is not a PDF."
      : undefined;

  const metadata: [string, string | number | null][] = [
    ["Document type", doc.documentType],
    ["Source", doc.sourceMode],
    ["Status", doc.status],
    ["Processing status", doc.processingStatus ?? "n/a"],
    ["Page count", doc.pageCount ?? "n/a"],
    ["Text extraction status", doc.textExtractionStatus ?? "not indexed"],
    ["Extraction warnings", doc.extractionWarningCount],
    ["Indexed at", doc.indexedAt ?? "not indexed"],
    ["Content type", doc.contentType ?? "n/a"],
    ["File size (bytes)", doc.fileSizeBytes ?? "n/a"],
    ["Revision label", doc.revisionLabel ?? "n/a"],
    ["Uploaded by", doc.uploadedByName ?? "n/a"],
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Document detail"
        title={doc.originalFileName ?? doc.fileName}
        description="Document metadata, intake state, and PDF page indexing. Indexing extracts embedded text from digital PDFs only. It does not OCR, approve, certify, verify, or validate anything."
      />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`${base}/documents`} className="nav-link">
            Back to documents
          </Link>
          <SourceBadge sourceMode={doc.sourceMode} />
          {doc.pageCount ? (
            <Link
              href={`${base}/documents/${doc.documentId}/pages`}
              className="nav-link"
            >
              View pages
            </Link>
          ) : null}
        </div>

        <SectionCard title="PDF page indexing">
          {doc.textExtractionSummary ? (
            <p className="mb-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
              {doc.textExtractionSummary}
            </p>
          ) : null}
          <IndexPdfButton
            projectId={params.projectId}
            documentId={doc.documentId}
            disabled={!canIndex}
            disabledReason={disabledReason}
          />
        </SectionCard>

        <SectionCard title="Document metadata">
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
        </SectionCard>
      </div>
    </div>
  );
}
