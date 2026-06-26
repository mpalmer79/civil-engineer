import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import { listProjects } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectsPage() {
  const projects = await listProjects("all");

  return (
    <div>
      <PageHeader
        eyebrow="Real project intake"
        title="Projects"
        description="Brookside Meadows remains the seeded guided demo. Real, user-created project records sit alongside it. Creating a project record is review-support only and does not approve plans or make engineering decisions."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm text-slate-600">
            {projects
              ? `${projects.length} project record${projects.length === 1 ? "" : "s"}`
              : "Project records are served by the backend."}
          </p>
          <Link
            href="/projects/new"
            className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700"
          >
            New project
          </Link>
        </div>

        {projects === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Project records are served by the backend. Start the API to create
              and view real project records. The Brookside Meadows guided demo
              remains available.
            </p>
          </SectionCard>
        ) : projects.length === 0 ? (
          <SectionCard title="No project records yet">
            <p className="text-sm text-slate-600">
              No project records exist yet. Create the first real project record
              to begin intake.
            </p>
          </SectionCard>
        ) : (
          <SectionCard>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">Project</th>
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Jurisdiction</th>
                    <th className="px-3 py-2">Review type</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Docs</th>
                    <th className="px-3 py-2">Findings</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr
                      key={p.projectId}
                      className="border-b border-slate-100 hover:bg-slate-50"
                    >
                      <td className="px-3 py-2">
                        <Link
                          href={`/projects/${p.projectId}`}
                          className="font-semibold text-water-700 hover:underline"
                        >
                          {p.projectName}
                        </Link>
                      </td>
                      <td className="px-3 py-2">
                        <SourceBadge sourceMode={p.sourceMode} />
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {p.jurisdiction || "Not specified"}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {p.reviewType}
                      </td>
                      <td className="px-3 py-2 text-slate-600">{p.status}</td>
                      <td className="px-3 py-2 text-slate-600">
                        {p.documentCount}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {p.findingCount}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        )}
      </div>
    </div>
  );
}
