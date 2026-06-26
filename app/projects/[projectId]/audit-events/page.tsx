import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import { getProjectDetail, listProjectAuditEvents } from "@/lib/api";

export const dynamic = "force-dynamic";

function metadataSummary(metadata: Record<string, unknown>): string {
  const entries = Object.entries(metadata).filter(
    ([, v]) => v !== null && v !== undefined && v !== "",
  );
  if (entries.length === 0) return "";
  return entries.map(([k, v]) => `${k}: ${String(v)}`).join(", ");
}

export default async function ProjectAuditEventsPage({
  params,
}: {
  params: { projectId: string };
}) {
  const [project, events] = await Promise.all([
    getProjectDetail(params.projectId),
    listProjectAuditEvents(params.projectId),
  ]);
  if (!project) {
    notFound();
  }
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
          <SectionCard title="No audit events yet">
            <p className="text-sm text-slate-600">
              No audit events have been recorded for this project record yet.
            </p>
          </SectionCard>
        ) : (
          <SectionCard>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">Timestamp</th>
                    <th className="px-3 py-2">Actor</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Event</th>
                    <th className="px-3 py-2">Related</th>
                    <th className="px-3 py-2">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((e) => (
                    <tr key={e.auditEventId} className="border-b border-slate-100 align-top">
                      <td className="px-3 py-2 text-slate-600">{e.timestamp}</td>
                      <td className="px-3 py-2 text-slate-700">
                        {e.actorDisplayName ?? "System"}
                      </td>
                      <td className="px-3 py-2 text-slate-600">{e.actorType}</td>
                      <td className="px-3 py-2 font-medium text-slate-800">
                        {e.eventType}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {e.relatedEntityType}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {e.description}
                        {metadataSummary(e.eventMetadata) ? (
                          <span className="mt-1 block text-xs text-slate-400">
                            {metadataSummary(e.eventMetadata)}
                          </span>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        )}
      </div>
    </div>
  );
}
