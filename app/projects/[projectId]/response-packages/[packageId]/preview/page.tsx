import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import { previewResponsePackage } from "@/lib/api";

export const dynamic = "force-dynamic";

// Response package preview. A printable-style, safe preview of the reviewer
// communication. It carries the fixed boundary statement and never exposes raw
// file paths, storage keys, signed URLs, or secrets. Nothing here approves,
// resolves, or closes anything.
export default async function ResponsePackagePreviewPage(
  props: {
    params: Promise<{ projectId: string; packageId: string }>;
  }
) {
  const params = await props.params;
  const preview = await previewResponsePackage(
    params.projectId,
    params.packageId,
  );
  if (!preview) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow="Response package preview"
        title={preview.packageTitle}
        description="A review-support preview of the reviewer communication. It does not finalize a review outcome, resolve issues, or close issues."
      />
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`${base}/response-packages/${params.packageId}`}
            className="nav-link"
          >
            Back to package
          </Link>
          <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
            Status: {preview.status}
          </span>
        </div>

        <div className="surface-card p-8">
          <p className="text-sm text-slate-500">
            Project: {preview.projectName}
          </p>
          <h2 className="mt-1 text-2xl font-bold text-slate-900">
            {preview.packageTitle}
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {preview.packageType.replace(/_/g, " ")} - Package{" "}
            {preview.packageNumber}, revision {preview.revisionNumber}
            {preview.issuedByName ? ` - Issued by ${preview.issuedByName}` : ""}
          </p>

          <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
            {preview.boundaryStatement}
          </p>

          {preview.items.length === 0 ? (
            <p className="mt-6 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              Add reviewer-selected records before previewing the package.
            </p>
          ) : (
            <ol className="mt-6 space-y-5">
              {preview.items.map((item, index) => (
                <li key={index} className="border-b border-slate-100 pb-4">
                  <p className="font-semibold text-slate-800">
                    Comment {item.itemNumber ?? index + 1}
                    {item.category ? ` - ${item.category}` : ""}
                  </p>
                  <p className="mt-1 text-sm text-slate-700">
                    {item.reviewerCommentText}
                  </p>
                  {item.requestedEvidence ? (
                    <p className="mt-1 text-sm text-slate-600">
                      Requested evidence: {item.requestedEvidence}
                    </p>
                  ) : null}
                  {item.applicantResponseSummary ? (
                    <p className="mt-1 text-sm text-slate-600">
                      Applicant response summary: {item.applicantResponseSummary}
                    </p>
                  ) : null}
                  {item.citationReference ? (
                    <p className="mt-1 text-sm text-slate-600">
                      Citation reference: {item.citationReference}
                    </p>
                  ) : null}
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </div>
  );
}
