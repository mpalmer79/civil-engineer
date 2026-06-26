import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import GuidedDemoThread from "@/components/GuidedDemoThread";

export default function GuidedDemoRoute() {
  return (
    <div>
      <PageHeader
        eyebrow="Guided demo"
        title="One issue, from checklist to draft response"
        description="Follow a single Brookside Meadows issue, the missing infiltration testing and groundwater separation concern, through the entire review-support workflow: the checklist requirement, the finding, its source evidence, the review packet item, the workflow board item, and the draft response package language. It ends at the human-review boundary. Civil Engineer AI organizes review-support evidence; it does not approve plans, certify compliance, verify CAD, validate design, or replace a licensed Professional Engineer."
      />

      <div className="mx-auto max-w-4xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="Why this thread">
          <p className="text-sm text-slate-600">
            Civil Engineer AI has many modules. This guided thread proves one
            complete workflow on a single concrete issue so you can see how a
            requirement, a finding, source evidence, a review packet, a workflow
            item, and draft response language connect, without needing to learn
            every module first. Each step links into the module where the live
            data is served by the backend.
          </p>
        </SectionCard>

        <GuidedDemoThread />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
