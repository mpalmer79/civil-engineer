import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import ResponsePackageBuilder from "@/components/ResponsePackageBuilder";

export default function ResponsePackagePage() {
  return (
    <div>
      <PageHeader
        eyebrow="External review response package"
        title="Brookside Meadows draft response package"
        description="Phase 10 turns ready-for-handoff workflow items into a structured draft external response package for an applicant, design engineer, municipal reviewer, or internal review team. It groups items by topic, drafts plain review-support wording, keeps evidence traceability, and builds an attachment checklist and a human review sign-off checklist. It does not send email, approve plans, certify compliance, stamp drawings, verify CAD, or validate the design."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What the response package builder does">
          <p className="text-sm text-slate-600">
            The builder assembles a draft response from the workflow board,
            groups items into topical sections, and lets a reviewer edit draft
            wording, manage item statuses, inspect linked evidence, review the
            attachment checklist, follow the package history, and open a
            printable draft. Every item stays under human review, and a licensed
            Professional Engineer remains responsible for the review. The package
            is built from seeded review-support data, not from parsed PDF, DWG,
            DXF, or Autodesk files, and the system does not send correspondence.
          </p>
        </SectionCard>

        <ResponsePackageBuilder />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
