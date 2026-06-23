import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import HumanReviewClient from "@/components/HumanReviewClient";

export default function HumanReviewPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Human review queue"
        title="Reviewer decisions on AI draft findings"
        description="Phase 5 routes every AI draft finding to a human reviewer. A reviewer can accept, edit, reject, escalate, mark unclear, or request more information. Each action is recorded with a reviewer note, applies a status transition, and writes audit events. No action approves, certifies, or declares a design compliant."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="How the review queue works">
          <ol className="grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              1. Run an AI review to generate draft findings on the AI Review
              page.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              2. Draft findings that pass validation arrive here as needing human
              review.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              3. The reviewer records an action with a note for the audit record.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              4. The draft finding status updates and the action is preserved in
              history.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              5. Failed drafts are shown separately and cannot be accepted.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              6. Accepted findings remain review-support findings, never final
              approvals.
            </li>
          </ol>
        </SectionCard>

        <HumanReviewClient />

        <SafetyBoundaryBanner />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Phase 5 note:</span>{" "}
          Review actions are recorded in the backend and are never faked in
          frontend-only mode. If the backend is not running, start the API to
          record actions. The system does not approve plans, certify compliance,
          or make final engineering decisions.
        </div>
      </div>
    </div>
  );
}
