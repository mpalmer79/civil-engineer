import PageHeader from "@/components/PageHeader";
import AuditTimeline from "@/components/AuditTimeline";
import SectionCard from "@/components/SectionCard";

export default function AuditPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Audit trail"
        title="Traceable review history"
        description="Every significant system and human action is recorded so any finding can be reconstructed end to end — from fixture load to evaluation scoring."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What the audit trail answers">
          <ul className="grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Which documents and checklist items were evaluated?
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              What evidence was mapped to each finding?
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Did safety-wording validation pass before a finding was shown?
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              What did the human reviewer decide, and when?
            </li>
          </ul>
        </SectionCard>

        <AuditTimeline />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Phase 1 note:</span>{" "}
          This timeline is seeded and illustrative. Later phases will record real
          system events (retrieval queries, model calls, prompt versions) and
          real human review actions.
        </div>
      </div>
    </div>
  );
}
