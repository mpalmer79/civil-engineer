import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import CadIntakePage from "@/components/CadIntakePage";
import { getProjectDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectCadPage(
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
        title="CAD intake and metadata"
        description="Reviewer-facing CAD intake for this project: upload and parse DXF files, inspect parse status, layers, text, blocks, and reference candidates, and promote CAD review-support findings into the workflow board. DXF parsing extracts metadata and references only. It does not verify CAD, validate design, certify compliance, or approve plans."
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
          <Link href={`${base}/command-center`} className="nav-link">
            Command center
          </Link>
        </div>

        <CadIntakePage projectId={project.projectId} />
      </div>
    </div>
  );
}
