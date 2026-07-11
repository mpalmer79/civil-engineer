import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import RequestFailureCard from "@/components/RequestFailureCard";
import { previewCommentLetter } from "@/lib/api";

export const dynamic = "force-dynamic";

// Comment letter preview. A printable-style, safe view of the reviewer
// communication draft. It carries the fixed boundary statement and never exposes
// raw paths, storage keys, signed URLs, or secrets. Nothing here approves,
// resolves, or closes anything.
export default async function CommentLetterPreviewPage(
  props: {
    params: Promise<{ projectId: string; draftId: string }>;
  }
) {
  const params = await props.params;
  const previewResult = await previewCommentLetter(params.projectId, params.draftId);
  if (!previewResult.ok) {
    if (previewResult.kind === "not_found") notFound();
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <RequestFailureCard failure={previewResult} />
      </div>
    );
  }
  const preview = previewResult.data;
  const base = `/projects/${params.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow="Comment letter preview"
        title={preview.title}
        description="A review-support preview of the reviewer communication draft. It does not finalize a review outcome, resolve issues, or close issues."
      />

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`${base}/comment-letter-drafts/${params.draftId}`}
            className="nav-link"
          >
            Back to draft
          </Link>
          <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
            Status: {preview.status}
          </span>
        </div>

        <div className="surface-card p-8">
          <h2 className="text-2xl font-bold text-slate-900">{preview.title}</h2>
          {preview.recipientName ? (
            <p className="mt-1 text-sm text-slate-500">
              To: {preview.recipientName}
              {preview.recipientOrganization
                ? `, ${preview.recipientOrganization}`
                : ""}
            </p>
          ) : null}

          <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
            {preview.boundaryStatement}
          </p>

          <div className="mt-6 space-y-5">
            {preview.sections.map((section, index) => (
              <div key={index}>
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                  {section.heading}
                </h3>
                <p className="mt-1 whitespace-pre-line text-sm text-slate-700">
                  {section.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
