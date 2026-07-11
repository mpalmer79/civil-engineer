import Link from "next/link";
import RequestFailureCard from "@/components/RequestFailureCard";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import CreateChecklistFromRulePack from "@/components/CreateChecklistFromRulePack";
import {
  getProjectDetail,
  listProjectChecklists,
  listRulePacks,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ProjectChecklistsPage(
  props: {
    params: Promise<{ projectId: string }>;
  }
) {
  const params = await props.params;
  const [projectResult, checklistsResult, rulePacksResult] = await Promise.all([
    getProjectDetail(params.projectId),
    listProjectChecklists(params.projectId),
    listRulePacks(),
  ]);
  if (!projectResult.ok) {
    if (projectResult.kind === "not_found") notFound();
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <RequestFailureCard failure={projectResult} />
      </div>
    );
  }
  const project = projectResult.data;
  const checklists = checklistsResult.ok ? checklistsResult.data : null;
  const rulePacks = rulePacksResult.ok ? rulePacksResult.data : null;
  const base = `/projects/${project.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Project checklists"
        description="Apply a reusable rule pack to this project as a review-support checklist. Checklist status is review-support only and requires human confirmation. It does not approve plans, certify compliance, or validate design."
      />

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href="/rule-packs" className="nav-link">
            Rule packs
          </Link>
        </div>

        <CreateChecklistFromRulePack
          projectId={project.projectId}
          rulePacks={(rulePacks ?? []).map((p) => ({
            rulePackId: p.rulePackId,
            name: p.name,
            itemCount: p.itemCount,
          }))}
        />

        {checklists === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Project checklists are served by the backend. Start the API to view
              them.
            </p>
          </SectionCard>
        ) : checklists.length === 0 ? (
          <SectionCard title="No checklist yet">
            <p className="text-sm text-slate-600">
              Create a checklist from a starter rule pack to begin
              checklist-driven review.
            </p>
          </SectionCard>
        ) : (
          <ul className="space-y-3">
            {checklists.map((c) => (
              <li key={c.projectChecklistId} className="surface-card p-5 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Link
                    href={`${base}/checklists/${c.projectChecklistId}`}
                    className="text-base font-semibold text-water-700 hover:underline"
                  >
                    {c.name}
                  </Link>
                  <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                    {c.status}
                  </span>
                </div>
                <p className="mt-2 text-slate-600">{c.itemCount} item(s)</p>
                {Object.keys(c.evidenceStatusSummary).length > 0 ? (
                  <p className="mt-1 text-xs text-slate-500">
                    Evidence status:{" "}
                    {Object.entries(c.evidenceStatusSummary)
                      .map(([status, count]) => `${status} (${count})`)
                      .join(", ")}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
