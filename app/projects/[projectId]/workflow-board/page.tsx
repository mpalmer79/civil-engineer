import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import BoundaryNote from "@/components/BoundaryNote";
import { getProjectDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

const WORKFLOW_BOUNDARY_NOTE =
  "The workflow board tracks reviewer-controlled review-support work items. It " +
  "does not approve plans or make engineering decisions.";

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
        description="This project workflow board surface is being prepared. It will surface existing reviewer workflow items as review-support work, not final decisions."
      />

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/command-center`} className="nav-link">
            Command center
          </Link>
        </div>

        <BoundaryNote note={WORKFLOW_BOUNDARY_NOTE} />

        <SectionCard title="Surface being prepared">
          <p className="text-sm text-slate-600">
            The project-scoped workflow board is being prepared in a later Phase
            3 pass. The command center already surfaces reviewer attention items
            and next steps. No workflow data is shown here yet.
          </p>
        </SectionCard>
      </div>
    </div>
  );
}
