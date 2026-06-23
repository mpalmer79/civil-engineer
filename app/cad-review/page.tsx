import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import CadReviewClient from "@/components/CadReviewClient";

export default function CadReviewPage() {
  return (
    <div>
      <PageHeader
        eyebrow="CAD-aware review"
        title="CAD-aware metadata and plan consistency review"
        description="Phase 6 connects document findings to plan sheet references and civil feature metadata. This page uses seeded CAD-aware metadata, not live CAD parsing. It surfaces missing sheets, conflicting labels, and references that need human review."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What CAD-aware review means here">
          <p className="text-sm text-slate-600">
            Civil Engineer AI does not parse CAD files, process DWG or DXF data,
            or integrate with Autodesk in this phase. It organizes plan sheet
            evidence and CAD-aware metadata for civil features (basins, pipes,
            roads, lots, utilities, and more) so a reviewer can trace how
            documents, sheets, and features connect. It does not verify CAD
            drawings or validate a design.
          </p>
        </SectionCard>

        <CadReviewClient />

        <SafetyBoundaryBanner />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Phase 6 note:</span>{" "}
          Plan consistency findings are review-support findings that require
          human review. They do not approve plans, certify compliance, verify
          CAD, or validate a design.
        </div>
      </div>
    </div>
  );
}
