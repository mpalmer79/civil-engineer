import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import CadReviewClient from "@/components/CadReviewClient";

const futureStages = [
  "Plan sheet PDF rendering for the sheet viewer",
  "Richer DXF entity extraction and structured plan exports beyond CAD Intake",
  "Autodesk Platform Services viewer exploration",
  "CAD and document cross-reference automation",
];

export default function CadReviewPage() {
  return (
    <div>
      <PageHeader
        eyebrow="CAD-aware review"
        title="CAD-aware metadata and plan consistency review"
        description="CAD Review organizes seeded and derived CAD-aware review metadata: it connects civil feature references to plan sheets and surfaces plan consistency findings that need reviewer confirmation. Real DXF upload and metadata extraction live in CAD Intake. CAD Review does not parse DWG, verify CAD, validate geometry, certify compliance, or approve plans."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What CAD-aware review means">
          <p className="text-sm text-slate-600">
            CAD Review organizes plan sheet evidence and civil feature references
            for a human reviewer. The civil feature metadata below is seeded or
            derived review-support metadata. Real DXF files are uploaded and
            parsed for extracted metadata in{" "}
            <a
              href="/cad-intake"
              className="font-semibold text-water-700 hover:text-water-600"
            >
              CAD Intake
            </a>
            ; this page focuses on organizing plan sheet and civil feature
            references rather than parsing drawings. The plan consistency check
            compares plan references against the plan sheet index to surface
            missing targets, conflicting labels, and unclear revisions. Civil
            Engineer AI does not parse DWG, verify CAD drawings, validate the
            design, or confirm compliance.
          </p>
        </SectionCard>

        <SafetyBoundaryBanner variant="compact" />

        <CadReviewClient />

        <SectionCard title="Future CAD and Autodesk integration path">
          <p className="text-sm text-slate-600">
            Civil Engineer AI prepares for staged CAD integration. None of the following is
            implemented yet, and no Autodesk integration exists today.
          </p>
          <ul className="mt-4 grid gap-3 sm:grid-cols-2">
            {futureStages.map((stage) => (
              <li
                key={stage}
                className="flex items-start gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700"
              >
                <span aria-hidden="true" className="mt-0.5 text-land-600">
                  ◆
                </span>
                {stage}
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>
    </div>
  );
}
