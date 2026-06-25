import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import ReviewCyclesClient from "@/components/ReviewCyclesClient";

export default function ReviewCyclesRoute() {
  return (
    <div>
      <PageHeader
        eyebrow="Resubmittal intake and revision cycle"
        title="Brookside Meadows review cycles"
        description="Phase 13 tracks multiple review rounds. A reviewer can create or load a review cycle, record a resubmittal package, link uploaded DXF files and applicant responses, compare current and previous DXF parse metadata, map applicant responses to prior response items, mark review-support resolution statuses, carry unresolved items forward, and prepare the next review cycle. Revision comparison compares extracted DXF metadata only. It does not verify CAD, validate design, approve plans, certify compliance, send correspondence, or replace a licensed Professional Engineer."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What review cycles do">
          <p className="text-sm text-slate-600">
            Civil Engineer AI organizes a multi-round municipal review workflow.
            After the initial review produces findings, a review packet, a
            workflow board, and a response package, the applicant returns a
            resubmittal. A reviewer records the resubmittal, links the revised DXF
            file and applicant response notes, runs a revision comparison against
            the previous DXF parse round, reviews added, removed, changed,
            unchanged, and carried-forward references, maps applicant responses to
            prior items, marks review-support resolution statuses, carries
            unresolved items forward, and prepares the next round. Every status is
            a review-support status under human review. The system does not
            approve plans, certify compliance, verify CAD, or validate design.
          </p>
        </SectionCard>

        <ReviewCyclesClient />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
