import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import GuidedDemoThread from "@/components/GuidedDemoThread";

export default function GuidedDemoPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Guided demo"
        title="One concern, end to end"
        description="Follow a single review-support concern, missing infiltration testing and an unaddressed groundwater separation discussion, from checklist requirement through finding, evidence, review packet, workflow board, and draft response, ending at the human-review boundary."
      />

      <div className="mx-auto max-w-4xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SafetyBoundaryBanner variant="compact" />
        <GuidedDemoThread />
        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
