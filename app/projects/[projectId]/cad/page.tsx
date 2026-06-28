import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import BoundaryNote from "@/components/BoundaryNote";
import { getProjectDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

const CAD_BOUNDARY_NOTE =
  "CAD intake and metadata are review-support records only. This system does " +
  "not verify CAD drawings or make engineering decisions.";

export default async function ProjectCadPage({
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
        title="CAD intake and metadata"
        description="This project CAD surface is being prepared. It will surface existing CAD intake and metadata records as review-support evidence."
      />

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/command-center`} className="nav-link">
            Command center
          </Link>
          <Link href={`${base}/plan-consistency`} className="nav-link">
            Plan consistency
          </Link>
        </div>

        <BoundaryNote note={CAD_BOUNDARY_NOTE} />

        <SectionCard title="Surface being prepared">
          <p className="text-sm text-slate-600">
            The project-scoped CAD intake and metadata view is being prepared in
            a later Phase 3 pass. Plan consistency findings already reference CAD
            metadata where it exists. No CAD data is shown here yet, and nothing
            on this page is a finding about drawing content.
          </p>
        </SectionCard>
      </div>
    </div>
  );
}
