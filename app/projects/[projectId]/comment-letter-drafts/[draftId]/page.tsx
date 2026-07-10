import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import CommentLetterEditor from "@/components/CommentLetterEditor";
import { getCommentLetterDraft } from "@/lib/api";

export const dynamic = "force-dynamic";

// Comment letter draft detail page. The reviewer edits each section and marks the
// draft ready for reviewer handoff. The draft is a deterministic, reviewer-
// editable communication artifact. It does not approve plans, certify compliance,
// resolve an issue, or close an issue.
export default async function CommentLetterDraftPage(
  props: {
    params: Promise<{ projectId: string; draftId: string }>;
  }
) {
  const params = await props.params;
  const draft = await getCommentLetterDraft(params.projectId, params.draftId);
  if (!draft) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow="Comment letter draft"
        title={draft.title}
        description="A deterministic, reviewer-editable comment letter draft generated from a response package. It does not finalize a review outcome, resolve issues, or close issues."
      />

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`${base}/response-packages/${draft.responsePackageId}`}
            className="nav-link"
          >
            Back to package
          </Link>
          <Link
            href={`${base}/comment-letter-drafts/${draft.commentLetterDraftId}/preview`}
            className="nav-link"
          >
            Preview comment letter
          </Link>
          <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
            Status: {draft.status}
          </span>
        </div>

        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {draft.boundaryStatement}
        </p>

        <CommentLetterEditor projectId={params.projectId} draft={draft} />
      </div>
    </div>
  );
}
