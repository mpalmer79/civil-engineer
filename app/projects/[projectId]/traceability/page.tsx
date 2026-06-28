import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import EmptyState from "@/components/EmptyState";
import BoundaryNote from "@/components/BoundaryNote";
import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import {
  getProjectDetail,
  getReviewPackets,
  getReviewPacketTraceability,
} from "@/lib/api";

export const dynamic = "force-dynamic";

const TRACE_BOUNDARY_NOTE =
  "Traceability is currently packet-based: it shows how a review packet links " +
  "requirements to evidence, sources, and review items. A linked row is " +
  "potential support that requires reviewer confirmation. It does not state " +
  "that a requirement is satisfied. Project-wide traceability beyond packets is " +
  "future work.";

export default async function ProjectTraceabilityPage({
  params,
}: {
  params: { projectId: string };
}) {
  const project = await getProjectDetail(params.projectId);
  if (!project) {
    notFound();
  }
  const base = `/projects/${project.projectId}`;
  const packets = await getReviewPackets(project.projectId);
  const packet = packets.length > 0 ? packets[0] : null;
  const traceability = packet
    ? await getReviewPacketTraceability(packet.packetId)
    : null;

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Traceability"
        description="How review packet requirements link to evidence, sources, and review items. Each linked row is potential support that requires reviewer confirmation, never a statement that a requirement is satisfied."
      />

      <div className="mx-auto max-w-6xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/review-packets`} className="nav-link">
            Review packets
          </Link>
          <Link href={`${base}/checklists`} className="nav-link">
            Project checklists
          </Link>
          <Link href={`${base}/command-center`} className="nav-link">
            Command center
          </Link>
        </div>

        <BoundaryNote note={TRACE_BOUNDARY_NOTE} />

        {packet === null ? (
          <EmptyState
            title="No review packet yet"
            description="Traceability is packet-based today. Generate a review packet to assemble requirement-to-evidence links. An absent packet does not mean requirements are satisfied or unsupported, only that no packet has been generated yet."
            action={
              <Link
                href={`${base}/review-packets`}
                className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700"
              >
                Go to review packets
              </Link>
            }
          />
        ) : traceability === null ? (
          <SectionCard title="Traceability unavailable">
            <p className="text-sm text-slate-600">
              The traceability matrix for packet{" "}
              <Link
                href={`${base}/review-packets`}
                className="text-water-700 hover:underline"
              >
                {packet.title}
              </Link>{" "}
              could not be loaded. Start the backend API to view it. This is a
              connection state, not a finding about the evidence.
            </p>
          </SectionCard>
        ) : traceability.rows.length === 0 ? (
          <EmptyState
            title="No linked evidence yet"
            description="This packet has no requirement-to-evidence links yet. That is not a statement that requirements are satisfied or unsupported; it means links have not been recorded yet."
          />
        ) : (
          <SectionCard
            title={`Traceability matrix (${traceability.rows.length} link(s))`}
            description={`Packet: ${packet.title}. Each row is a recorded link that requires reviewer confirmation.`}
          >
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-2 pr-4">Requirement / item</th>
                    <th className="py-2 pr-4">Section</th>
                    <th className="py-2 pr-4">Linked evidence</th>
                    <th className="py-2 pr-4">Source</th>
                    <th className="py-2 pr-4">Relationship</th>
                  </tr>
                </thead>
                <tbody>
                  {traceability.rows.map((row, index) => (
                    <tr
                      key={`${row.itemId}:${row.evidenceId}:${index}`}
                      className="border-b border-slate-100 align-top"
                    >
                      <td className="py-2 pr-4">
                        <span className="font-medium text-slate-800">
                          {row.itemTitle}
                        </span>
                        <span className="block text-xs text-slate-500">
                          {humanizeStatus(row.itemType)}
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-slate-600">
                        {humanizeStatus(row.sectionType)}
                      </td>
                      <td className="py-2 pr-4 text-slate-700">
                        {row.label || row.evidenceId}
                        <span className="block text-xs text-slate-500">
                          {humanizeStatus(row.evidenceType)}
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-xs text-slate-500">
                        {row.sourceId ? (
                          <>
                            {humanizeStatus(row.sourceType)}
                            <span className="block">{row.sourceId}</span>
                          </>
                        ) : (
                          <span className="text-slate-400">
                            source link unavailable
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-4">
                        <StatusChip label={humanizeStatus(row.relationship)} />
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
