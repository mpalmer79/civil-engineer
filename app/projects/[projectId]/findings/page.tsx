import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import RiskBadge from "@/components/RiskBadge";
import {
  getProjectDetail,
  listProjectEvidenceCitations,
  listProjectFindings,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectFindingsPage({
  params,
}: {
  params: { projectId: string };
}) {
  const [project, findings, citations] = await Promise.all([
    getProjectDetail(params.projectId),
    listProjectFindings(params.projectId),
    listProjectEvidenceCitations(params.projectId),
  ]);
  if (!project) {
    notFound();
  }
  const base = `/projects/${project.projectId}`;
  const citationCount = (findingId: string) =>
    (citations ?? []).filter((c) => c.findingId === findingId).length;

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Reviewer findings"
        description="Seeded demo findings appear for Brookside Meadows. Reviewer-created review-support findings appear for real project records. Every finding requires human confirmation and is not a final engineering conclusion."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between gap-4">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link
            href={`${base}/findings/new`}
            className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700"
          >
            Create finding
          </Link>
        </div>

        {findings === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Findings are served by the backend. Start the API to view and
              create review-support findings.
            </p>
          </SectionCard>
        ) : findings.length === 0 ? (
          <SectionCard title="No findings yet">
            <p className="text-sm text-slate-600">
              No review-support findings exist for this project record yet.
            </p>
          </SectionCard>
        ) : (
          <div className="space-y-4">
            {findings.map((f) => (
              <SectionCard key={f.findingId}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-base font-semibold text-slate-900">
                    <Link
                      href={`${base}/findings/${f.findingId}`}
                      className="text-water-700 hover:underline"
                    >
                      {f.title}
                    </Link>
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                      {citationCount(f.findingId)} citation
                      {citationCount(f.findingId) === 1 ? "" : "s"}
                    </span>
                    <RiskBadge
                      level={
                        (["high", "medium", "low"].includes(f.riskLevel)
                          ? f.riskLevel
                          : "low") as "high" | "medium" | "low"
                      }
                    />
                    <SourceBadge sourceMode={f.sourceMode} />
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
                  <span>
                    <span className="font-semibold text-slate-500">Category:</span>{" "}
                    {f.category}
                  </span>
                  <span>
                    <span className="font-semibold text-slate-500">
                      Evidence status:
                    </span>{" "}
                    {f.evidenceStatus ?? "n/a"}
                  </span>
                  <span>
                    <span className="font-semibold text-slate-500">
                      Human review status:
                    </span>{" "}
                    {f.humanReviewStatus}
                  </span>
                  <span>
                    <span className="font-semibold text-slate-500">Origin:</span>{" "}
                    {f.findingOrigin}
                  </span>
                  <span>
                    <span className="font-semibold text-slate-500">
                      Created by:
                    </span>{" "}
                    {f.createdByName ?? "Seeded demo"}
                  </span>
                </div>
                {f.recommendedHumanAction ? (
                  <p className="mt-2 text-sm text-slate-700">
                    <span className="font-semibold text-slate-500">
                      Recommended human action:
                    </span>{" "}
                    {f.recommendedHumanAction}
                  </p>
                ) : null}
                {f.relatedDocuments.length > 0 ? (
                  <p className="mt-1 text-xs text-slate-500">
                    Related documents: {f.relatedDocuments.join(", ")}
                  </p>
                ) : null}
              </SectionCard>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
