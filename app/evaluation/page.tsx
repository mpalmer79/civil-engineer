import PageHeader from "@/components/PageHeader";
import EvaluationSummary from "@/components/EvaluationSummary";
import SectionCard from "@/components/SectionCard";
import { getEvaluationData } from "@/lib/api";

export default async function EvaluationPage() {
  const { cases, summary } = await getEvaluationData();
  return (
    <div>
      <PageHeader
        eyebrow="Evaluation dashboard"
        title="Evaluation-driven AI design"
        description="Eight evaluation cases test whether the system surfaces the expected findings, cites real evidence, avoids false positives, and never emits prohibited wording."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="Why evaluation comes first">
          <p className="text-sm text-slate-600">
            An evaluation harness is the difference between a serious GenAI system
            and a demo. Each case isolates one meaningful behavior, from
            detecting a missing infiltration test to staying silent on a clean
            control package, and is scored against expected findings.
          </p>
        </SectionCard>

        <EvaluationSummary evaluationCases={cases} evaluationSummary={summary} />

        <SectionCard
          title="Phase 4 AI review validation metrics"
          description="The AI Review Assistant tracks these signals on each run. Phase 5 will score them against expected findings in a live evaluation harness."
        >
          <ul className="grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Draft finding schema validity (validation passed rate)
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Source chunk citation validity
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Prohibited wording count (target zero)
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Human review requirement rate (target 100 percent)
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Validation failure count and safety check failure count
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Expected finding match rate against the seeded planted issues
            </li>
          </ul>
        </SectionCard>

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Prototype note:</span>{" "}
          This dashboard displays seeded evaluation outcomes with mock but
          plausible values. Phase 5 will run evaluation cases against generated
          draft findings and compute these metrics live.
        </div>
      </div>
    </div>
  );
}
