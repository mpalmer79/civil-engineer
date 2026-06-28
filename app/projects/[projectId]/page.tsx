import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import SourceBadge from "@/components/SourceBadge";
import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import ProjectWorkloadCard from "@/components/ProjectWorkloadCard";
import DemoNoteCard from "@/components/DemoNoteCard";
import { priorityLabel } from "@/lib/dashboardLabels";
import { BROOKSIDE_PROJECT_ID } from "@/lib/demoJourney";
import { getProjectDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectDetailPage({
  params,
}: {
  params: { projectId: string };
}) {
  const project = await getProjectDetail(params.projectId);
  if (!project) {
    notFound();
  }

  const base = `/projects/${project.projectId}`;
  const metadata: [string, string | number | null][] = [
    ["Project type", project.projectType],
    ["Jurisdiction", project.jurisdiction || "Not specified"],
    ["Review type", project.reviewType],
    ["Review domain", project.reviewDomain],
    ["Location context", project.locationContext || "Not specified"],
    ["Acreage", project.acreage],
    ["Disturbed area", project.disturbedArea],
    ["Proposed lots", project.proposedLots],
    ["Applicant", project.applicantName ?? "Not specified"],
    ["Applicant organization", project.applicantOrganization ?? "Not specified"],
    ["Design engineer", project.designEngineerName ?? "Not specified"],
    ["Design firm", project.designFirm ?? "Not specified"],
    ["Submission reference", project.submissionReference ?? "Not specified"],
    ["Review round", project.reviewRoundCurrent],
    ["Created by", project.createdByName ?? "Seeded demo"],
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Project overview"
        title={project.projectName}
        description={project.summary || "Review-support project record."}
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        {project.projectId === BROOKSIDE_PROJECT_ID ? (
          <DemoNoteCard
            message="You are viewing the Brookside Meadows sample project, a synthetic public demo record. This page shows how reviewers track evidence and workflow state."
            actionHref="/guided-demo"
            actionLabel="Open the guided demo"
          />
        ) : null}

        <div className="flex flex-wrap items-center gap-2">
          <SourceBadge sourceMode={project.sourceMode} />
          <StatusChip prefix="Status:" label={humanizeStatus(project.status)} />
          <StatusChip
            prefix="Review priority:"
            label={priorityLabel(project.reviewPriority)}
          />
          <StatusChip
            prefix="Assigned reviewer:"
            label={project.assignedReviewerName ?? "Not set"}
          />
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <MetricCard value={project.documentCount} label="Documents" accent="water" />
          <MetricCard value={project.findingCount} label="Findings" accent="amber" />
          <MetricCard
            value={project.auditEventCount}
            label="Audit events"
            accent="slate"
          />
        </div>

        <ProjectWorkloadCard projectId={project.projectId} />

        <SectionCard
          title="Analytical surfaces"
          description="Review-support analytical screens that surface existing backend computation for this project. Each is review-support only and does not make engineering decisions."
        >
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            <Link href={`${base}/command-center`} className="menu-item">
              Command center
            </Link>
            <Link href={`${base}/plan-consistency`} className="menu-item">
              Plan consistency
            </Link>
            <Link href={`${base}/plan-sheets`} className="menu-item">
              Plan sheets
            </Link>
            <Link href={`${base}/traceability`} className="menu-item">
              Traceability
            </Link>
            <Link href={`${base}/cad`} className="menu-item">
              CAD intake and metadata
            </Link>
            <Link href={`${base}/workflow-board`} className="menu-item">
              Workflow board
            </Link>
            <Link href={`${base}/review-packets`} className="menu-item">
              Review packets
            </Link>
          </div>
        </SectionCard>

        <SectionCard
          title="Project workflow"
          description="Reviewer-controlled workflow areas for this project record. Each opens a review-support screen where human review continues."
        >
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            <Link href={`${base}/workload`} className="menu-item">
              Project workload
            </Link>
            <Link href={`${base}/documents`} className="menu-item">
              Documents
            </Link>
            <Link href={`${base}/documents/register`} className="menu-item">
              Register document
            </Link>
            <Link href={`${base}/findings`} className="menu-item">
              Reviewer findings
            </Link>
            <Link href={`${base}/findings/new`} className="menu-item">
              Create finding
            </Link>
            <Link href={`${base}/evidence-citations`} className="menu-item">
              Evidence citations
            </Link>
            <Link href={`${base}/evidence-search`} className="menu-item">
              Evidence search
            </Link>
            <Link href={`${base}/evidence-candidates`} className="menu-item">
              Evidence candidate queue
            </Link>
            <Link href={`${base}/checklists`} className="menu-item">
              Project checklists
            </Link>
            <Link href={`${base}/response-matrix`} className="menu-item">
              Response matrix
            </Link>
            <Link href={`${base}/resubmittals`} className="menu-item">
              Resubmittal rounds
            </Link>
            <Link href={`${base}/response-packages`} className="menu-item">
              Response packages
            </Link>
            <Link href="/rule-packs" className="menu-item">
              Rule packs
            </Link>
            <Link href={`${base}/access`} className="menu-item">
              Project access
            </Link>
            <Link href={`${base}/audit-events`} className="menu-item">
              Audit events
            </Link>
          </div>
        </SectionCard>

        <SectionCard title="Project metadata">
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            {metadata.map(([label, value]) => (
              <div key={label} className="flex justify-between gap-4 border-b border-slate-100 pb-2">
                <dt className="text-sm font-semibold text-slate-500">{label}</dt>
                <dd className="text-sm text-slate-800">{value}</dd>
              </div>
            ))}
          </dl>
          {project.parcelIds.length > 0 ? (
            <p className="mt-3 text-sm text-slate-600">
              <span className="font-semibold text-slate-700">Parcel IDs:</span>{" "}
              {project.parcelIds.join(", ")}
            </p>
          ) : null}
        </SectionCard>

        <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          This project record is review-support only. It does not approve plans,
          certify compliance, verify CAD, validate design, or make final
          engineering decisions. Every item requires human review.
        </p>
      </div>
    </div>
  );
}
