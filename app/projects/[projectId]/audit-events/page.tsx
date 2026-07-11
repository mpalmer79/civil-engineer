import Link from "next/link";
import RequestFailureCard from "@/components/RequestFailureCard";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
import { getProjectDetail, listProjectAuditEvents } from "@/lib/api";

export const dynamic = "force-dynamic";

function metadataSummary(metadata: Record<string, unknown>): string {
  const entries = Object.entries(metadata).filter(
    ([, v]) => v !== null && v !== undefined && v !== "",
  );
  if (entries.length === 0) return "";
  return entries.map(([k, v]) => `${k}: ${String(v)}`).join(", ");
}

export default async function ProjectAuditEventsPage(
  props: {
    params: Promise<{ projectId: string }>;
  }
) {
  const params = await props.params;
  const [projectResult, eventsResult] = await Promise.all([
    getProjectDetail(params.projectId),
    listProjectAuditEvents(params.projectId),
  ]);
  if (!projectResult.ok) {
    if (projectResult.kind === "not_found") notFound();
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <RequestFailureCard failure={projectResult} />
      </div>
    );
  }
  const project = projectResult.data;
  const events = eventsResult.ok ? eventsResult.data : null;
  const base = `/projects/${project.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Audit events"
        description="Durable audit events recorded from real actions on this project record. Events show who did what and when. They never store raw IP addresses, raw user agents, or secrets."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <Link href={base} className="nav-link">
          Back to project
        </Link>

        {events === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Audit events are served by the backend. Start the API to view the
              project history.
            </p>
          </SectionCard>
        ) : events.length === 0 ? (
          <EmptyState
            title="No audit events yet"
            description="No audit events have been recorded for this project record yet."
          />
        ) : (
          <ul className="list-container">
            {events.map((e) => (
              <li key={e.auditEventId} className="flex flex-col gap-2 px-4 py-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold text-slate-800">
                    {e.eventType}
                  </span>
                  <span className="text-xs text-slate-500">{e.timestamp}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  <StatusChip
                    label={e.actorDisplayName ?? "System"}
                    prefix="actor"
                  />
                  <StatusChip label={e.actorType} prefix="role" />
                  <StatusChip label={e.relatedEntityType} prefix="related" />
                </div>
                <p className="text-sm text-slate-600">
                  {e.description}
                  {metadataSummary(e.eventMetadata) ? (
                    <span className="mt-1 block text-xs text-slate-400">
                      {metadataSummary(e.eventMetadata)}
                    </span>
                  ) : null}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
