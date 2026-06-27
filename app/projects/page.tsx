import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import SignInNotice from "@/components/SignInNotice";
import EmptyState from "@/components/EmptyState";
import ProjectsDashboardCards from "@/components/ProjectsDashboardCards";
import { listProjects, type ProjectDetail } from "@/lib/api";

export const dynamic = "force-dynamic";

// A single, responsive project row. One DOM node that reads as a table-style
// row on wider screens and stacks cleanly on mobile, so long project names and
// status chips stay readable without horizontal scrolling.
function ProjectRow({ project }: { project: ProjectDetail }) {
  return (
    <div className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <Link
          href={`/projects/${project.projectId}`}
          className="break-words text-sm font-semibold text-water-700 hover:underline"
        >
          {project.projectName}
        </Link>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500">
          <span>{project.jurisdiction || "Jurisdiction not specified"}</span>
          <span aria-hidden="true">·</span>
          <span>{project.reviewType}</span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <SourceBadge sourceMode={project.sourceMode} />
        <StatusChip prefix="Status:" label={humanizeStatus(project.status)} />
        <span className="chip chip-neutral">
          {project.documentCount} docs
        </span>
        <span className="chip chip-neutral">
          {project.findingCount} findings
        </span>
      </div>
    </div>
  );
}

export default async function ProjectsPage() {
  const projects = await listProjects("all");
  const demoProjects =
    projects?.filter((p) => p.sourceMode === "demo_fixture") ?? [];
  const realProjects =
    projects?.filter((p) => p.sourceMode !== "demo_fixture") ?? [];

  return (
    <div>
      <PageHeader
        eyebrow="Real project intake"
        title="Projects"
        description="A review-support workspace for stormwater plan review. The seeded Brookside Meadows guided demo sits alongside real, user-created project records. Creating a project record is review-support only and does not approve plans or make engineering decisions."
        actions={
          <Link href="/projects/new" className="btn btn-primary">
            Create project record
          </Link>
        }
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SignInNotice />
        <ProjectsDashboardCards />

        {projects === null ? (
          <div className="alert alert-warning" role="alert">
            <p className="font-semibold">Backend required</p>
            <p className="mt-1">
              Project records are served by the backend. Start the API to create
              and view real project records. The Brookside Meadows guided demo
              remains available.
            </p>
          </div>
        ) : (
          <>
            {/* Real project records, kept visually separate from the public
                guided demo so the two are never confused. */}
            <section className="space-y-3">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="section-eyebrow">Real project records</p>
                  <h2 className="text-lg font-semibold text-slate-900">
                    {realProjects.length} real project record
                    {realProjects.length === 1 ? "" : "s"}
                  </h2>
                </div>
                <Link href="/projects/new" className="btn btn-secondary btn-sm">
                  New project
                </Link>
              </div>
              {realProjects.length === 0 ? (
                <EmptyState
                  title="No real project records yet"
                  description="Create the first real project record to begin document-first, evidence-first stormwater review. The public Brookside Meadows demo stays available below."
                  action={
                    <Link href="/projects/new" className="btn btn-primary">
                      Create project record
                    </Link>
                  }
                />
              ) : (
                <div className="list-container">
                  {realProjects.map((project) => (
                    <ProjectRow key={project.projectId} project={project} />
                  ))}
                </div>
              )}
            </section>

            {/* Public guided demo. Always available, no account required. */}
            {demoProjects.length > 0 ? (
              <section className="space-y-3">
                <div>
                  <p className="section-eyebrow">Public guided demo</p>
                  <h2 className="text-lg font-semibold text-slate-900">
                    Brookside Meadows
                  </h2>
                  <p className="mt-1 max-w-2xl text-sm text-slate-600">
                    A seeded review-support demo subdivision. It is available
                    without an account and is clearly labeled as a demo fixture.
                  </p>
                </div>
                <div className="list-container">
                  {demoProjects.map((project) => (
                    <ProjectRow key={project.projectId} project={project} />
                  ))}
                </div>
              </section>
            ) : null}
          </>
        )}

        <SectionCard className="bg-slate-50">
          <p className="text-sm text-slate-600">
            Project records support human plan review. They do not approve
            plans, certify compliance, verify CAD, validate design, or make final
            engineering decisions. Every item requires human review.
          </p>
        </SectionCard>
      </div>
    </div>
  );
}
