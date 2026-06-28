import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import EmptyState from "@/components/EmptyState";
import BoundaryNote from "@/components/BoundaryNote";
import TraceabilityMatrix from "@/components/TraceabilityMatrix";
import { getProjectDetail, getProjectTraceability } from "@/lib/api";

export const dynamic = "force-dynamic";

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
  const traceability = await getProjectTraceability(project.projectId);

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Traceability"
        description="Project-wide review-support traceability. It organizes existing links between checklist requirements, evidence, findings, workflow items, and review packets. It does not determine whether a requirement is satisfied; every row requires reviewer confirmation."
      />

      <div className="mx-auto max-w-7xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/checklists`} className="nav-link">
            Project checklists
          </Link>
          <Link href={`${base}/evidence-search`} className="nav-link">
            Evidence search
          </Link>
          <Link href={`${base}/review-packets`} className="nav-link">
            Review packets
          </Link>
          <Link href={`${base}/command-center`} className="nav-link">
            Command center
          </Link>
        </div>

        {traceability === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Project traceability is served by the backend. Start the API to
              load it. This is a connection state, not a finding about the
              project.
            </p>
          </SectionCard>
        ) : (
          <>
            <BoundaryNote note={traceability.limitationsNote} />

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
              <MetricCard
                value={traceability.summary.totalChecklistItems}
                label="Checklist items"
              />
              <MetricCard
                value={traceability.summary.checklistItemsWithLinkedEvidence}
                label="With linked evidence"
              />
              <MetricCard
                value={traceability.summary.checklistItemsWithoutLinkedEvidence}
                label="No linked evidence yet"
                accent={
                  traceability.summary.checklistItemsWithoutLinkedEvidence > 0
                    ? "amber"
                    : "slate"
                }
              />
              <MetricCard
                value={traceability.summary.totalTraceabilityRows}
                label="Traceability rows"
              />
              <MetricCard
                value={
                  traceability.summary.rowsRequiringReviewerConfirmation
                }
                label="Need reviewer confirmation"
                accent={
                  traceability.summary.rowsRequiringReviewerConfirmation > 0
                    ? "amber"
                    : "slate"
                }
              />
            </div>

            {!traceability.hasIndexedInformation ? (
              <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                This project has no indexed, searchable document pages yet, so
                some rows show not enough indexed information. Index documents and
                build page chunks to surface more linked evidence. This is a
                workflow state, not a finding about the project.
              </p>
            ) : null}

            <SectionCard
              title="Packet-based traceability"
              description="Review packets also provide their own requirement-to-evidence traceability. Open a review packet to view its packet traceability tab."
            >
              <Link
                href={`${base}/review-packets`}
                className="text-sm font-semibold text-water-700 hover:underline"
              >
                Open review packets
              </Link>
            </SectionCard>

            {traceability.rows.length === 0 ? (
              <EmptyState
                title="No traceability rows yet"
                description="No project checklist items are recorded yet. Create a checklist from a rule pack to begin linking requirements to evidence. An absent matrix does not mean requirements are satisfied or unsupported."
                action={
                  <Link
                    href={`${base}/checklists`}
                    className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700"
                  >
                    Go to checklists
                  </Link>
                }
              />
            ) : (
              <TraceabilityMatrix
                projectId={project.projectId}
                rows={traceability.rows}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
