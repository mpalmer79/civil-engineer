import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import ReviewerFindingForm from "@/components/ReviewerFindingForm";

export default function NewFindingPage({
  params,
}: {
  params: { projectId: string };
}) {
  return (
    <div>
      <PageHeader
        eyebrow="Real project intake"
        title="Create reviewer finding"
        description="Create a reviewer-owned review-support finding for this project record. This is a review-support finding requiring human confirmation. It does not approve, certify, verify, resolve, or close anything."
      />
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Link href={`/projects/${params.projectId}/findings`} className="nav-link">
          Back to findings
        </Link>
        <ReviewerFindingForm projectId={params.projectId} />
      </div>
    </div>
  );
}
