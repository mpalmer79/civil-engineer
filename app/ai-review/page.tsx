import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import AiReviewClient from "@/components/AiReviewClient";

export default function AiReviewPage() {
  return (
    <div>
      <PageHeader
        eyebrow="AI Review Assistant"
        title="Controlled AI review with retrieved evidence"
        description="Civil Engineer AI runs a constrained AI review workflow. For each checklist item the backend retrieves source evidence, builds a constrained prompt from that evidence only, validates the structured output, runs safety checks, and saves a draft review-support finding that requires human review."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="How the AI review works">
          <ol className="grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              1. Load applicable checklist items for Brookside Meadows.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              2. Retrieve source evidence chunks for each checklist item.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              3. Build a constrained prompt using only retrieved evidence.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              4. Call the provider (mock by default, live optional and disabled).
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              5. Validate the JSON schema and run safety and citation checks.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              6. Save a draft finding that requires human review, and write audit
              events.
            </li>
          </ol>
        </SectionCard>

        <AiReviewClient />

        <SafetyBoundaryBanner />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Note:</span>{" "}
          The default provider is a deterministic mock, so the workflow runs
          without any API key. Optional live provider configuration is documented
          in the notes below. The AI does not approve plans, certify
          compliance, or make final engineering decisions.
        </div>
      </div>
    </div>
  );
}
