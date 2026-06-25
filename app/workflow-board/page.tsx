import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import WorkflowBoardClient from "@/components/WorkflowBoardClient";

export default function WorkflowBoardPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Reviewer workflow board"
        title="Brookside Meadows reviewer workflow board"
        description="Civil Engineer AI promotes the review packet items into an operational board so a human reviewer can triage each item, request follow-up or more information, record reviewer notes, mark items reviewer checked or excluded, and mark items ready for handoff to a licensed Professional Engineer. The board organizes review-support work. It does not approve plans, certify compliance, stamp drawings, verify CAD, or validate the design."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What the workflow board does">
          <p className="text-sm text-slate-600">
            The board groups review-support items into workflow columns, tracks
            every status transition and reviewer note, records follow-up
            requests, and shows which items a reviewer has marked ready for
            handoff. Every item stays under human control, and a licensed
            Professional Engineer remains responsible for the review. The board
            is built from seeded review-support data, not from parsed PDF, DWG,
            DXF, or Autodesk files.
          </p>
        </SectionCard>

        <WorkflowBoardClient />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
