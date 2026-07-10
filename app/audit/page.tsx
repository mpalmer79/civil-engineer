import DataSourceNotice from "@/components/DataSourceNotice";
import PageHeader from "@/components/PageHeader";
import AuditTimeline from "@/components/AuditTimeline";
import SectionCard from "@/components/SectionCard";
import { getAuditEvents } from "@/lib/api";

export default async function AuditPage() {
  const eventsResult = await getAuditEvents();
  const events = eventsResult.data;
  return (
    <div>
      <PageHeader
        eyebrow="Audit trail"
        title="Traceable review history"
        description="Every significant system and human action is recorded so any finding can be reconstructed end to end, from fixture load to evaluation scoring."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <DataSourceNotice source={eventsResult.source} />
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

        <AuditTimeline events={events} />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Demo note:</span>{" "}
          This timeline shows the seeded Brookside Meadows events. Authenticated
          project work writes real audit events with reviewer attribution; see
          the project audit history inside a signed-in workspace.
        </div>
      </div>
    </div>
  );
}
