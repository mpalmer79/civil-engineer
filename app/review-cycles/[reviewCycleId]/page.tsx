import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import ReviewCycleSummaryCard from "@/components/ReviewCycleSummaryCard";
import NextCyclePreparationPanelReadOnly from "@/components/NextCyclePreparationReadOnly";
import { getReviewCycle, getNextCyclePreparation } from "@/lib/api";

export default async function ReviewCycleDetailRoute({
  params,
}: {
  params: { reviewCycleId: string };
}) {
  const [cycle, preparation] = await Promise.all([
    getReviewCycle(params.reviewCycleId),
    getNextCyclePreparation(params.reviewCycleId),
  ]);

  return (
    <div>
      <PageHeader
        eyebrow="Review cycle detail"
        title={cycle ? cycle.cycleName : "Review cycle"}
        description="A single review round for Brookside Meadows. This view is review-support only and does not approve plans, certify compliance, verify CAD, or validate design."
      />

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Link
          href="/review-cycles"
          className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
        >
          Back to review cycles
        </Link>

        {cycle ? (
          <ReviewCycleSummaryCard cycle={cycle} />
        ) : (
          <div className="surface-card p-6 text-sm text-slate-500">
            Review cycle not found, or the backend is not reachable.
          </div>
        )}

        <NextCyclePreparationPanelReadOnly preparation={preparation} />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
