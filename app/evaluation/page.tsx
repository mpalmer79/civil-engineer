import PageHeader from "@/components/PageHeader";
import EvaluationSummary from "@/components/EvaluationSummary";
import EvaluationScoringClient from "@/components/EvaluationScoringClient";
import MetricCard from "@/components/MetricCard";
import SectionCard from "@/components/SectionCard";
import { getEvaluationData, getPlanConsistencySummary } from "@/lib/api";

export default async function EvaluationPage() {
  const { cases, summary } = await getEvaluationData();
  const planSummary = await getPlanConsistencySummary();
  return (
    <div>
      <PageHeader
        eyebrow="Evaluation dashboard"
        title="Evaluation-driven AI design"
        description="Phase 5 scores AI draft findings against the expected Brookside Meadows findings. The dashboard reports recall, precision, citation validity, human review required rate, and validation and safety failure counts."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="Phase 5 evaluation scoring">
          <p className="text-sm text-slate-600">
            Evaluation scoring compares the draft findings from an AI review run
            against the expected findings using related checklist items,
            category, and title overlap. It calculates recall and precision,
            checks source citation validity, and counts prohibited wording,
            validation failures, and safety failures. The matching is
            heuristic and explainable, not a final engineering determination.
          </p>
        </SectionCard>

        <EvaluationScoringClient />

        <SectionCard
          title="Phase 6 plan consistency review"
          description="Plan-sheet-specific review-support findings from the seeded plan set, CAD-aware metadata, and plan references. These findings require human review and are not a design validation."
        >
          {planSummary ? (
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
              <MetricCard
                value={planSummary.totalFindings}
                label="Plan consistency findings"
                accent="water"
              />
              <MetricCard
                value={planSummary.missingSheetCount}
                label="Missing sheet count"
                accent={planSummary.missingSheetCount > 0 ? "red" : "land"}
              />
              <MetricCard
                value={planSummary.conflictingLabelCount}
                label="Conflicting label count"
                accent={planSummary.conflictingLabelCount > 0 ? "amber" : "land"}
              />
              <MetricCard
                value={planSummary.cadMetadataRecords}
                label="CAD-aware metadata records"
                accent="water"
              />
              <MetricCard
                value={planSummary.planReferencesRequiringHumanReview}
                label="Plan references requiring human review"
                accent="amber"
              />
            </div>
          ) : (
            <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
              The backend is not reachable. Plan consistency metrics load from
              the API. See the CAD Review page to run a plan consistency check.
            </p>
          )}
        </SectionCard>

        <SectionCard title="Why evaluation matters">
          <p className="text-sm text-slate-600">
            An evaluation harness is the difference between a serious GenAI system
            and a demo. Each seeded evaluation case below isolates one meaningful
            behavior, from detecting a missing infiltration test to staying
            silent on a clean control package, and is scored against expected
            findings.
          </p>
        </SectionCard>

        <EvaluationSummary evaluationCases={cases} evaluationSummary={summary} />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Scope note:</span>{" "}
          The seeded evaluation cases above describe expected behaviors with
          plausible reference values. The Phase 5 scoring panel above computes
          live recall, precision, and citation metrics from a real AI review run
          and stores each result in the backend.
        </div>
      </div>
    </div>
  );
}
