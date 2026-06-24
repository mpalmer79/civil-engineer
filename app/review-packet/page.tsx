import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import ReviewPacketBuilder from "@/components/ReviewPacketBuilder";

export default function ReviewPacketPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Review packet builder"
        title="Brookside Meadows review-support packet"
        description="Phase 8 assembles documents, checklist items, findings, plan sheets, CAD-aware metadata, hotspots, plan consistency findings, human review actions, and audit evidence into a structured review-support packet draft. The packet organizes evidence for a human reviewer. It does not approve plans, certify compliance, stamp drawings, verify CAD, or validate the design."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What the review packet builder does">
          <p className="text-sm text-slate-600">
            The packet draft groups review evidence into sections, links each
            item back to its source entities, and offers an evidence
            traceability matrix and a printable review-support summary. Every
            item requires human review, and a licensed Professional Engineer
            remains responsible for the review. The packet is built from seeded
            review-support data, not from parsed PDF, DWG, DXF, or Autodesk
            files.
          </p>
        </SectionCard>

        <ReviewPacketBuilder />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
