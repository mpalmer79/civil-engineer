import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import CadIntakePage from "@/components/CadIntakePage";

export default function CadIntakeRoute() {
  return (
    <div>
      <PageHeader
        eyebrow="Browser CAD upload and parse review queue"
        title="Brookside Meadows DXF intake and parsing"
        description="Civil Engineer AI lets a reviewer upload a real DXF file through the browser, validate it, request a parse, inspect parse status and parse failures, view a CAD intake dashboard and parse queue, review unpromoted CAD findings, and promote selected CAD findings into the workflow board. DXF parsing extracts metadata and references only. It does not verify CAD, validate geometry or design, certify compliance, approve plans, or replace a licensed Professional Engineer. DXF is the only supported file type; DWG parsing is future work."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What CAD intake does">
          <p className="text-sm text-slate-600">
            Upload a DXF file from the browser. The system validates the file
            (extension, size, content type, and readability), stores it under a
            safe generated file name, and parses it on request. It surfaces the
            extracted layers, text, blocks, and reference candidates with
            confidence labels and human-review flags, and raises review-support
            findings when a referenced sheet has no match, a detail reference is
            ambiguous, a basin label may conflict, or a layer cannot be
            categorized. A reviewer can promote selected findings into the
            workflow board, and the system prevents duplicate workflow items from
            the same finding. DXF parsing extracts metadata and references only;
            it does not verify CAD or validate the design.
          </p>
        </SectionCard>

        <CadIntakePage />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
