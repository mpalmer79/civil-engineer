import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import EmptyState from "@/components/EmptyState";
import BoundaryNote from "@/components/BoundaryNote";
import CountByCategoryBar from "@/components/CountByCategoryBar";
import RiskBadge from "@/components/RiskBadge";
import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import RunPlanConsistencyCheckButton from "@/components/RunPlanConsistencyCheckButton";
import PlanConsistencyFindingActions from "@/components/PlanConsistencyFindingActions";
import {
  getPlanConsistencyFindings,
  getPlanConsistencyReviewActions,
  getPlanConsistencySummary,
  getProjectDetail,
  type PlanConsistencyFinding,
  type PlanConsistencyReviewAction,
} from "@/lib/api";

export const dynamic = "force-dynamic";

const RISK_LEVELS = new Set(["high", "medium", "low"]);

const PLAN_BOUNDARY_NOTE =
  "Plan consistency findings are review-support findings that require reviewer " +
  "confirmation. They are potential issues for a human reviewer, not final " +
  "engineering conclusions. This view does not perform final design review or " +
  "make engineering decisions.";

function RiskLabel({ level }: { level: string }) {
  if (RISK_LEVELS.has(level)) {
    return <RiskBadge level={level as "high" | "medium" | "low"} />;
  }
  return <StatusChip label={humanizeStatus(level)} prefix="risk:" />;
}

function RelatedIds({
  label,
  ids,
  hrefFor,
  unavailableNote,
}: {
  label: string;
  ids: string[];
  hrefFor?: (id: string) => string;
  unavailableNote?: string;
}) {
  if (ids.length === 0) return null;
  return (
    <div className="mt-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {ids.map((id) =>
          hrefFor ? (
            <Link
              key={id}
              href={hrefFor(id)}
              className="rounded-md bg-water-50 px-2 py-1 text-xs font-medium text-water-700 hover:bg-water-100"
            >
              {id}
            </Link>
          ) : (
            <span
              key={id}
              title={unavailableNote ?? "Link not available yet"}
              className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-500"
            >
              {id}
            </span>
          ),
        )}
      </div>
    </div>
  );
}

function FindingCardItem({
  finding,
  base,
  history,
}: {
  finding: PlanConsistencyFinding;
  base: string;
  history: PlanConsistencyReviewAction[];
}) {
  return (
    <li className="surface-card p-4 text-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <span className="font-semibold text-slate-800">{finding.title}</span>
        <div className="flex flex-wrap items-center gap-2">
          <RiskLabel level={finding.riskLevel} />
          <StatusChip label={humanizeStatus(finding.status)} />
        </div>
      </div>
      <p className="mt-1 text-xs text-slate-500">
        {humanizeStatus(finding.findingType)}
      </p>
      {finding.summary ? (
        <p className="mt-2 text-slate-600">{finding.summary}</p>
      ) : null}
      {finding.recommendedHumanAction ? (
        <p className="mt-2 text-sm text-slate-700">
          <span className="font-semibold">Reviewer action: </span>
          {finding.recommendedHumanAction}
        </p>
      ) : null}
      <RelatedIds
        label="Related documents"
        ids={finding.relatedDocumentIds}
        hrefFor={(id) => `${base}/documents/${id}`}
      />
      <RelatedIds
        label="Related checklist items"
        ids={finding.relatedChecklistItems}
        hrefFor={() => `${base}/checklists`}
      />
      <RelatedIds
        label="Related CAD metadata"
        ids={finding.relatedCadMetadataIds}
        hrefFor={() => `${base}/cad`}
      />
      <RelatedIds
        label="Related sheets"
        ids={finding.relatedSheetIds}
        hrefFor={(id) => `${base}/plan-sheets/${id}`}
      />
      <PlanConsistencyFindingActions
        planFindingId={finding.planFindingId}
        history={history}
      />
    </li>
  );
}

export default async function PlanConsistencyPage({
  params,
}: {
  params: { projectId: string };
}) {
  const project = await getProjectDetail(params.projectId);
  if (!project) {
    notFound();
  }
  const base = `/projects/${project.projectId}`;
  const [summary, findings, reviewActions] = await Promise.all([
    getPlanConsistencySummary(project.projectId),
    getPlanConsistencyFindings(project.projectId),
    getPlanConsistencyReviewActions(undefined, project.projectId),
  ]);
  const actionsByFinding = new Map<string, PlanConsistencyReviewAction[]>();
  for (const action of reviewActions) {
    const list = actionsByFinding.get(action.planFindingId) ?? [];
    list.push(action);
    actionsByFinding.set(action.planFindingId, list);
  }

  return (
    <div>
      <PageHeader
        eyebrow={project.projectName}
        title="Plan consistency"
        description="Review-support consistency checks across plan sheets, plan references, and CAD metadata. Findings are potential issues that require reviewer confirmation, not final engineering conclusions."
      />

      <div className="mx-auto max-w-6xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap gap-2">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/command-center`} className="nav-link">
            Command center
          </Link>
          <Link href={`${base}/documents`} className="nav-link">
            Documents
          </Link>
          <Link href={`${base}/checklists`} className="nav-link">
            Project checklists
          </Link>
        </div>

        <BoundaryNote note={PLAN_BOUNDARY_NOTE} />

        {summary === null ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Plan consistency data is served by the backend. Start the API to
              load this project&rsquo;s plan consistency summary and findings.
              This is a connection state, not a finding about plan content.
            </p>
          </SectionCard>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              <MetricCard value={summary.totalSheets} label="Total sheets" />
              <MetricCard
                value={summary.missingSheetCount}
                label="Missing sheets"
                accent={summary.missingSheetCount > 0 ? "amber" : "slate"}
              />
              <MetricCard
                value={summary.cadMetadataRecords}
                label="CAD metadata records"
              />
              <MetricCard
                value={summary.totalPlanReferences}
                label="Plan references"
              />
              <MetricCard
                value={summary.inconsistentReferences}
                label="Inconsistent references"
                accent={summary.inconsistentReferences > 0 ? "amber" : "slate"}
              />
              <MetricCard
                value={summary.planConsistencyFindings}
                label="Findings"
              />
              <MetricCard
                value={summary.requiresHumanReviewCount}
                label="Need reviewer review"
                accent={summary.requiresHumanReviewCount > 0 ? "amber" : "slate"}
              />
            </div>

            <SectionCard
              title="Counts by finding type"
              description="Relative counts of the review-support finding types this check produced."
            >
              <CountByCategoryBar
                items={[
                  {
                    label: "Conflicting labels",
                    count: summary.conflictingLabelCount,
                    tone: "amber",
                  },
                  {
                    label: "Missing referenced sheet",
                    count: summary.missingReferencedSheetCount,
                    tone: "amber",
                  },
                  {
                    label: "Missing plan reference",
                    count: summary.missingPlanReferenceCount,
                    tone: "amber",
                  },
                  {
                    label: "Unclear revision",
                    count: summary.unclearRevisionCount,
                    tone: "water",
                  },
                ]}
                emptyText="No finding-type counts to show yet."
              />
            </SectionCard>

            <SectionCard
              title="Run the consistency check"
              description="Re-run the deterministic plan consistency check for this project. It refreshes review-support findings and never makes a final decision."
            >
              <RunPlanConsistencyCheckButton projectId={project.projectId} />
            </SectionCard>

            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Plan consistency findings
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Each finding requires reviewer confirmation. Recording a review
                action keeps the finding a review-support finding under human
                control; there is no approve action and nothing here finalizes a
                review outcome.
              </p>
              {findings.length === 0 ? (
                <div className="mt-3">
                  <EmptyState
                    title="No plan consistency findings yet"
                    description="Run the consistency check to produce review-support findings. An empty result is a workflow state, not a finding about plan content."
                  />
                </div>
              ) : (
                <ul className="mt-3 space-y-3">
                  {findings.map((finding) => (
                    <FindingCardItem
                      key={finding.planFindingId}
                      finding={finding}
                      base={base}
                      history={actionsByFinding.get(finding.planFindingId) ?? []}
                    />
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
