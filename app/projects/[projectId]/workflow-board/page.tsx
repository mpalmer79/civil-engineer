import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import WorkflowBoardClient from "@/components/WorkflowBoardClient";
import { getProjectDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectWorkflowBoardPage({
  params,
}: {
  params: { projectId: string };
}) {
  const project = await getProjectDetail(params.projectId);
  if (!project) {
    notFound();
  }
  const base = `/projects/${project.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Workflow board"
        description="Reviewer-controlled review-support work items for this project, grouped by status with severity, section, assigned role, follow-ups, and ready-for-handoff tracking. Every status is a review-support status, not a final engineering decision."
      />

      <div className="mx-auto max-w-7xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/command-center`} className="nav-link">
            Command center
          </Link>
          <Link href={`${base}/cad`} className="nav-link">
            CAD intake
          </Link>
          <Link href={`${base}/review-packets`} className="nav-link">
            Review packets
          </Link>
        </div>

        <WorkflowBoardClient projectId={project.projectId} />
      </div>
    </div>
  );
}
