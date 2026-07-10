import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import ProjectDashboard from "@/components/ProjectDashboard";
import { getProjectDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectCommandCenterPage(
  props: {
    params: Promise<{ projectId: string }>;
  }
) {
  const params = await props.params;
  const project = await getProjectDetail(params.projectId);
  if (!project) {
    notFound();
  }
  const base = `/projects/${project.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Command center"
        description="Aggregated review-support state for this project: attention items, readiness checks, timeline, next steps, and module links. Every status is a review-support status, not a final engineering decision."
      />

      <div className="mx-auto max-w-7xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/plan-consistency`} className="nav-link">
            Plan consistency
          </Link>
          <Link href={`${base}/workflow-board`} className="nav-link">
            Workflow board
          </Link>
          <Link href={`${base}/review-packets`} className="nav-link">
            Review packets
          </Link>
          <Link href={`${base}/traceability`} className="nav-link">
            Traceability
          </Link>
          <Link href={`${base}/documents`} className="nav-link">
            Documents
          </Link>
        </div>

        <ProjectDashboard projectId={project.projectId} />
      </div>
    </div>
  );
}
