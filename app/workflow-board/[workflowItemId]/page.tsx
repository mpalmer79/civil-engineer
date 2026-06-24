import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import WorkflowBoardClient from "@/components/WorkflowBoardClient";

export default function WorkflowItemDetailPage({
  params,
}: {
  params: { workflowItemId: string };
}) {
  return (
    <div>
      <PageHeader
        eyebrow="Reviewer workflow board"
        title="Workflow item"
        description="Inspect a single workflow item in the context of the full board, review its linked evidence and follow-up requests, record reviewer actions, and track its history. The board does not approve plans, certify compliance, verify CAD, or validate the design."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <Link
          href="/workflow-board"
          className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
        >
          Back to workflow board
        </Link>

        <WorkflowBoardClient initialItemId={params.workflowItemId} />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
