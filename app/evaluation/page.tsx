import PageHeader from "@/components/PageHeader";
import EvaluationSummary from "@/components/EvaluationSummary";
import SectionCard from "@/components/SectionCard";

export default function EvaluationPage() {
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
            and a demo. Each case isolates one meaningful behavior — from
            detecting a missing infiltration test to staying silent on a clean
            control package — and is scored against expected findings.
          </p>
        </SectionCard>

        <EvaluationSummary />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Phase 1 note:</span>{" "}
          This dashboard displays seeded evaluation outcomes with mock but
          plausible values. Later phases will run evaluation cases against
          generated findings and compute these metrics live.
        </div>
      </div>
    </div>
  );
}
