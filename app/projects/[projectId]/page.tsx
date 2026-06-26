import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import SourceBadge from "@/components/SourceBadge";
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
        <div className="flex flex-wrap items-center gap-3">
          <SourceBadge sourceMode={project.sourceMode} />
          <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
            Status: {project.status}
          </span>
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

        <div className="flex flex-wrap gap-2">
          <Link href={`${base}/documents`} className="nav-link">
            Documents
          </Link>
          <Link href={`${base}/documents/register`} className="nav-link">
            Register document
          </Link>
          <Link href={`${base}/findings`} className="nav-link">
            Reviewer findings
          </Link>
          <Link href={`${base}/findings/new`} className="nav-link">
            Create finding
          </Link>
          <Link href={`${base}/evidence-citations`} className="nav-link">
            Evidence citations
          </Link>
          <Link href={`${base}/evidence-search`} className="nav-link">
            Evidence search
          </Link>
          <Link href={`${base}/evidence-candidates`} className="nav-link">
            Evidence candidate queue
          </Link>
          <Link href={`${base}/audit-events`} className="nav-link">
            Audit events
          </Link>
        </div>

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
