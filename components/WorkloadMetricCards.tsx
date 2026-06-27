import MetricCard from "@/components/MetricCard";
import type { DashboardMetrics } from "@/lib/api";

// Presentational grid of review-support workload metrics. Every label is
// review-support only. None implies approval, certification, compliance,
// verification, or issue resolution.
export default function WorkloadMetricCards({
  metrics,
}: {
  metrics: DashboardMetrics;
}) {
  const cards: {
    value: number;
    label: string;
    accent: "slate" | "water" | "land" | "amber" | "red";
  }[] = [
    {
      value: metrics.pendingReviewerActionCount,
      label: "Pending reviewer action",
      accent: "amber",
    },
    {
      value: metrics.documentsNeedingIndexing,
      label: "Documents needing indexing",
      accent: "water",
    },
    {
      value: metrics.documentsIndexedWithText,
      label: "Documents indexed with text",
      accent: "slate",
    },
    {
      value: metrics.documentsExtractionUnavailable,
      label: "Extraction unavailable",
      accent: "slate",
    },
    {
      value: metrics.findingsNeedingReviewerConfirmation,
      label: "Findings needing reviewer confirmation",
      accent: "amber",
    },
    {
      value: metrics.evidenceCandidatesNeedingTriage,
      label: "Evidence candidates needing triage",
      accent: "water",
    },
    {
      value: metrics.checklistItemsMissingEvidence,
      label: "Checklist items with missing evidence",
      accent: "amber",
    },
    {
      value: metrics.checklistItemsUnclearEvidence,
      label: "Checklist items with unclear evidence",
      accent: "amber",
    },
    {
      value: metrics.applicantResponsesNeedingReview,
      label: "Applicant responses needing reviewer review",
      accent: "water",
    },
    {
      value: metrics.matrixItemsCarriedForward,
      label: "Carried forward for review",
      accent: "slate",
    },
    {
      value: metrics.responsePackagesReadyForHandoff,
      label: "Packages ready for reviewer handoff",
      accent: "land",
    },
    {
      value: metrics.packagesIssuedByReviewer,
      label: "Issued by reviewer",
      accent: "land",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {cards.map((card) => (
        <MetricCard
          key={card.label}
          value={card.value}
          label={card.label}
          accent={card.accent}
        />
      ))}
    </div>
  );
}
