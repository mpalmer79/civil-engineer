import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import ReviewPacketBuilder from "@/components/ReviewPacketBuilder";
import { getProjectDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectReviewPacketsPage(
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
        title="Review packets"
        description="Organized review-support evidence for this project: packet sections, items, evidence links, a traceability matrix, and a print view. Packets are drafts that require reviewer confirmation and do not certify compliance or make engineering decisions."
      />

      <div className="mx-auto max-w-7xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/command-center`} className="nav-link">
            Command center
          </Link>
          <Link href={`${base}/workflow-board`} className="nav-link">
            Workflow board
          </Link>
          <Link href={`${base}/traceability`} className="nav-link">
            Traceability
          </Link>
          <Link href={`${base}/response-packages`} className="nav-link">
            Response packages
          </Link>
        </div>

        <ReviewPacketBuilder projectId={project.projectId} />
      </div>
    </div>
  );
}
