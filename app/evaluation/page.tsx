import PageHeader from "@/components/PageHeader";
import EvaluationSummary from "@/components/EvaluationSummary";
import EvaluationScoringClient from "@/components/EvaluationScoringClient";
import SectionCard from "@/components/SectionCard";
import { getEvaluationData } from "@/lib/api";

export default async function EvaluationPage() {
  const { cases, summary } = await getEvaluationData();
  return (
    <div>
      <PageHeader
        eyebrow="Evaluation dashboard"
        title="Evaluation-driven AI design"
        description="Phase 5 scores AI draft findings against the expected Brookside Meadows findings, reporting recall, precision, citation validity, prohibited wording, and validation and safety failures. The seeded evaluation cases remain for reference."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard
          title="Phase 5 evaluation scoring"
          description="Run scoring against the latest AI review run. Results are stored in the backend with an explainable match table."
        >
          <p className="text-sm text-slate-600">
            Each draft finding is matched to an expected finding using its
            related checklist item, category, or title keyword overlap. Recall is
            matched expected findings divided by total expected findings.
            Precision is matched draft findings divided by total valid draft
            findings. Failed drafts are counted separately and never count as
            matches.
          </p>
        </SectionCard>

        <EvaluationScoringClient />

        <SectionCard title="Why evaluation matters">
          <p className="text-sm text-slate-600">
            An evaluation harness is the difference between a serious GenAI system
            and a demo. Each case isolates one meaningful behavior, from
            detecting a missing infiltration test to staying silent on a clean
            control package, and is scored against expected findings.
          </p>
        </SectionCard>

        <SectionCard
          title="Seeded evaluation cases (reference)"
          description="These eight seeded cases describe the behaviors the system should exhibit. Phase 5 live scoring above runs against generated draft findings."
        >
          <EvaluationSummary
            evaluationCases={cases}
            evaluationSummary={summary}
          />
        </SectionCard>

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Scope note:</span>{" "}
          Phase 5 evaluation scoring is a transparent, heuristic comparison of
          draft findings against expected findings. It is a quality signal for
          human reviewers. It does not certify the AI, approve the package, or
          declare the design compliant.
        </div>
      </div>
    </div>
  );
}
