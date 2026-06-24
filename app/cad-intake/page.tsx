import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import CadIntakePage from "@/components/CadIntakePage";

export default function CadIntakeRoute() {
  return (
    <div>
      <PageHeader
        eyebrow="Real CAD file intake"
        title="Brookside Meadows DXF intake and parsing"
        description="Phase 11 parses a real DXF file with the ezdxf library and extracts review-support metadata: layers, entities, blocks, text, reference candidates, and review-support findings. It compares extracted sheet and detail references against the seeded plan sheets. It does not verify CAD, validate geometry or design, certify compliance, approve plans, or replace a licensed Professional Engineer. DXF is the only supported file type; DWG parsing is future work."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What CAD intake does">
          <p className="text-sm text-slate-600">
            Intake registers a real DXF file, parses it, and surfaces the
            extracted layers, text, blocks, and reference candidates with
            confidence labels and human-review flags. It raises review-support
            findings when a referenced sheet has no match, a detail reference is
            ambiguous, a basin label may conflict, or a layer cannot be
            categorized, and it can create workflow items from those findings.
            This phase is backend fixture-based DXF parsing using the bundled
            Brookside Meadows sample; browser upload is a later enhancement.
          </p>
        </SectionCard>

        <CadIntakePage />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
