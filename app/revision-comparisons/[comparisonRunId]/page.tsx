import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import RevisionComparisonSummaryCard from "@/components/RevisionComparisonSummaryCard";
import RevisionChangeTable from "@/components/RevisionChangeTable";
import { getRevisionComparison, getRevisionChanges } from "@/lib/api";

export default async function RevisionComparisonDetailRoute(
  props: {
    params: Promise<{ comparisonRunId: string }>;
  }
) {
  const params = await props.params;
  const [run, changes] = await Promise.all([
    getRevisionComparison(params.comparisonRunId),
    getRevisionChanges(params.comparisonRunId),
  ]);

  return (
    <div>
      <PageHeader
        eyebrow="Revision comparison detail"
        title="DXF metadata revision comparison"
        description="A review-support comparison of extracted DXF metadata between two parse rounds. It compares layers, references, blocks, and review findings only. It does not verify CAD geometry or validate engineering design."
      />

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Link
          href="/review-cycles"
          className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
        >
          Back to review cycles
        </Link>

        <RevisionComparisonSummaryCard run={run} />

        <div className="surface-card p-6">
          <h3 className="text-lg font-semibold text-slate-900">
            Revision changes
          </h3>
          <div className="mt-4">
            <RevisionChangeTable changes={changes} />
          </div>
        </div>

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
