import Image from "next/image";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import SignInNotice from "@/components/SignInNotice";
import EmptyState from "@/components/EmptyState";
import ProjectsDashboardCards from "@/components/ProjectsDashboardCards";
import { listProjects, type ProjectDetail } from "@/lib/api";
import { projectMedia } from "@/lib/projectMedia";

export const dynamic = "force-dynamic";

function ProjectMedia({
  src,
  alt,
  className = "",
}: {
  src: string;
  alt: string;
  className?: string;
}) {
  return (
    <div className={`relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card ${className}`}>
      <Image
        src={src}
        alt={alt}
        fill
        sizes="(min-width: 1024px) 50vw, 100vw"
        className="object-cover"
      />
    </div>
  );
}

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

function ProjectVisualCard({ project }: { project: ProjectDetail }) {
  return (
    <Link href={`/projects/${project.projectId}`} className="interactive-card block overflow-hidden">
      <div className="relative h-52 w-full">
        <Image
          src={projectMedia.brooksideThumbnail.src}
          alt={projectMedia.brooksideThumbnail.alt}
          fill
          sizes="(min-width: 1024px) 33vw, 100vw"
          className="object-cover"
        />
      </div>
      <div className="p-5">
        <div className="flex flex-wrap items-center gap-2">
          <SourceBadge sourceMode={project.sourceMode} />
          <StatusChip prefix="Status:" label={humanizeStatus(project.status)} />
        </div>
        <h3 className="mt-3 text-base font-semibold text-slate-900">
          {project.projectName}
        </h3>
        <p className="mt-1 text-sm text-slate-600">
          {project.jurisdiction || "Jurisdiction not specified"} · {project.reviewType}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="chip chip-neutral">{project.documentCount} docs</span>
          <span className="chip chip-neutral">{project.findingCount} findings</span>
          <span className="chip chip-brand">Open project</span>
        </div>
      </div>
    </Link>
  );
}

export default async function ProjectsPage() {
  const projects = await listProjects("all");
  const demoProjects =
    projects?.filter((p) => p.sourceMode === "demo_fixture") ?? [];
  const realProjects =
    projects?.filter((p) => p.sourceMode !== "demo_fixture") ?? [];
  const brooksideProject = demoProjects[0];

  return (
    <div>
      <PageHeader
        eyebrow="Project workspace"
        title="Projects"
        description="Organize stormwater review records, open the Brookside Meadows sample project, and start new document-first review workspaces."
        actions={
          <Link href="/projects/new" className="btn btn-primary">
            Create project record
          </Link>
        }
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <section className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div>
            <span className="chip chip-brand">Projects workspace</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
              Review records with visual context
            </h2>
            <p className="mt-3 max-w-xl text-slate-600">
              Start with the Brookside Meadows sample project or create a real
              project record for document intake, page-level evidence, findings,
              applicant responses, and reviewer packages.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link href="/projects/new" className="btn btn-primary">
                Create project record
              </Link>
              <Link href="/start-here" className="btn btn-secondary">
                Start Here
              </Link>
              <Link href="/guided-demo" className="btn btn-secondary">
                Guided Demo
              </Link>
            </div>
          </div>
          <ProjectMedia
            src={projectMedia.hero.src}
            alt={projectMedia.hero.alt}
            className="h-72 lg:h-80"
          />
        </section>

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
            {demoProjects.length > 0 ? (
              <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-stretch">
                <ProjectVisualCard project={brooksideProject} />
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
                  <div className="surface-card p-5">
                    <span className="chip chip-neutral">Public guided demo</span>
                    <h2 className="mt-3 text-lg font-semibold text-slate-900">
                      Brookside Meadows
                    </h2>
                    <p className="mt-2 text-sm text-slate-600">
                      A seeded review-support demo subdivision. It is available
                      without an account and shows the reviewer journey with
                      sample documents, findings, checklist items, and response
                      workflow records.
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <Link href="/start-here" className="btn btn-primary btn-sm">
                        Start the walkthrough
                      </Link>
                      <Link href="/guided-demo" className="btn btn-secondary btn-sm">
                        Guided demo
                      </Link>
                    </div>
                  </div>
                  <ProjectMedia
                    src={projectMedia.documentsPreview.src}
                    alt={projectMedia.documentsPreview.alt}
                    className="min-h-56"
                  />
                </div>
              </section>
            ) : null}

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
                <div className="surface-card overflow-hidden p-0">
                  <div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
                    <ProjectMedia
                      src={projectMedia.emptyProjects.src}
                      alt={projectMedia.emptyProjects.alt}
                      className="h-64 rounded-none border-0 shadow-none lg:h-full"
                    />
                    <div className="p-6 lg:p-8">
                      <EmptyState
                        title="No real project records yet"
                        description="Create the first real project record to begin document-first, evidence-first stormwater review. The public Brookside Meadows demo stays available above."
                        action={
                          <Link href="/projects/new" className="btn btn-primary">
                            Create project record
                          </Link>
                        }
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="list-container">
                  {realProjects.map((project) => (
                    <ProjectRow key={project.projectId} project={project} />
                  ))}
                </div>
              )}
            </section>
          </>
        )}

        <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <ProjectMedia
            src={projectMedia.reviewSnapshot.src}
            alt={projectMedia.reviewSnapshot.alt}
            className="h-72"
          />
          <SectionCard className="bg-slate-50">
            <span className="chip chip-brand">Review snapshot</span>
            <h2 className="mt-3 text-lg font-semibold text-slate-900">
              See project progress at a glance
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Project records bring documents, findings, checklist progress,
              applicant responses, and reviewer communication records into one
              workspace. Indicators are operational review-support signals only.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="chip chip-neutral">Documents</span>
              <span className="chip chip-neutral">Findings</span>
              <span className="chip chip-neutral">Responses</span>
              <span className="chip chip-neutral">Dashboard</span>
            </div>
          </SectionCard>
        </section>

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
