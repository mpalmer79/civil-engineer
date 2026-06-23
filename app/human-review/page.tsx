import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import HumanReviewClient from "@/components/HumanReviewClient";

export default function HumanReviewPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Human review queue"
        title="Reviewer actions on AI draft findings"
        description="Phase 5 persists human review actions. A reviewer can accept, edit, reject, escalate, mark unclear, or request more information on each AI draft finding. Every action records a status transition and an audit event, and no action approves or certifies the work."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="How human review works">
          <ol className="grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              1. The AI review run produces draft findings that require human
              review.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              2. A reviewer inspects the finding and its source evidence.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              3. The reviewer records an action with a required note.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              4. The draft finding status transitions and the action is stored.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              5. Failed drafts can be rejected, escalated, or marked unclear, but
              never accepted.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              6. Every action writes an audit event for the decision history.
            </li>
          </ol>
        </SectionCard>

        <HumanReviewClient />

        <SafetyBoundaryBanner />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Phase 5 note:</span>{" "}
          Review actions are persisted by the backend. If the API is not
          running, the queue and actions are unavailable and review actions are
          never simulated in the browser. No action approves a plan, certifies
          compliance, or makes a final engineering decision.
        </div>
      </div>
    </div>
  );
}
