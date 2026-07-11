import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import ReviewCycleSummaryCard from "@/components/ReviewCycleSummaryCard";
import NextCyclePreparationPanelReadOnly from "@/components/NextCyclePreparationReadOnly";
import RequestFailureCard from "@/components/RequestFailureCard";
import { getReviewCycle, getNextCyclePreparation } from "@/lib/api";

export default async function ReviewCycleDetailRoute(
  props: {
    params: Promise<{ reviewCycleId: string }>;
  }
) {
  const params = await props.params;
  const [cycleResult, preparationResult] = await Promise.all([
    getReviewCycle(params.reviewCycleId),
    getNextCyclePreparation(params.reviewCycleId),
  ]);

  return (
    <div>
      <PageHeader
        eyebrow="Review cycle detail"
        title={cycleResult.ok ? cycleResult.data.cycleName : "Review cycle"}
        description="A single review round for Brookside Meadows. This view is review-support only and does not approve plans, certify compliance, verify CAD, or validate design."
      />

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Link
          href="/review-cycles"
          className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
        >
          Back to review cycles
        </Link>

        {cycleResult.ok ? (
          <ReviewCycleSummaryCard cycle={cycleResult.data} />
        ) : (
          <RequestFailureCard failure={cycleResult} />
        )}

        {preparationResult.ok ? (
          <NextCyclePreparationPanelReadOnly
            preparation={preparationResult.data}
          />
        ) : (
          <RequestFailureCard failure={preparationResult} />
        )}

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
