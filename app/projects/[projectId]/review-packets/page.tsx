import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import BoundaryNote from "@/components/BoundaryNote";
import { getProjectDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

const PACKET_BOUNDARY_NOTE =
  "Review packets organize review-support evidence for a human reviewer. They " +
  "do not certify compliance or make engineering decisions.";

export default async function ProjectReviewPacketsPage({
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
        title="Review packets"
        description="This project review packets surface is being prepared. It will surface existing review packet records as organized review-support evidence."
      />

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/command-center`} className="nav-link">
            Command center
          </Link>
          <Link href={`${base}/response-packages`} className="nav-link">
            Response packages
          </Link>
        </div>

        <BoundaryNote note={PACKET_BOUNDARY_NOTE} />

        <SectionCard title="Surface being prepared">
          <p className="text-sm text-slate-600">
            The project-scoped review packets view is being prepared in a later
            Phase 3 pass. Response packages are already available for this
            project. No review packet data is shown here yet.
          </p>
        </SectionCard>
      </div>
    </div>
  );
}
