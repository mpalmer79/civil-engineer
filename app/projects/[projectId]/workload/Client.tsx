"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import WorkloadMetricCards from "@/components/WorkloadMetricCards";
import ReviewerQueueList from "@/components/ReviewerQueueList";
import ProjectWorkloadControls from "@/components/ProjectWorkloadControls";
import PermissionDeniedCard from "@/components/PermissionDeniedCard";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import {
  ageBucketLabel,
  dueDateIndicatorLabel,
  priorityLabel,
} from "@/lib/dashboardLabels";
import {
  getProjectWorkloadSummary,
  type ProjectWorkloadSummary,
} from "@/lib/api";

export default function ProjectWorkloadPageClient({ projectId }: { projectId: string }) {
  const [data, setData] = useState<ProjectWorkloadSummary | null>(null);
  const [denied, setDenied] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [backendReachable, setBackendReachable] = useState(true);

  useEffect(() => {
    let active = true;
    getProjectWorkloadSummary(projectId).then((result) => {
      if (!active) return;
      setBackendReachable(result.backendReachable);
      if (result.ok && result.data) setData(result.data);
      else if (result.status === 401 || result.status === 403) setDenied(true);
      setLoaded(true);
    });
    return () => {
      active = false;
    };
  }, [projectId]);

  const base = `/projects/${projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow="Project workload"
        title={data ? `Workload for ${data.projectName}` : "Project workload"}
        description="A single-project view of review-support workload: documents, findings, evidence, checklist, response matrix, resubmittal, and response package indicators, plus pending reviewer actions. Counts are operational indicators only and do not represent approval, compliance, or issue resolution."
      />

      <div className="mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <BackendStatusBanner />

        <div className="flex flex-wrap items-center gap-3">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href="/dashboard" className="nav-link">
            Reviewer dashboard
          </Link>
        </div>

        {loaded && denied ? (
          <PermissionDeniedCard message="You do not have access to this project's workload summary. Ask a project admin or organization admin for access." />
        ) : null}

        {loaded && !data && !denied && !backendReachable ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Project workload is served by the backend. Start the API to view
              it.
            </p>
          </SectionCard>
        ) : null}

        {data ? (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <StatusChip prefix="Status:" label={humanizeStatus(data.status)} />
              <StatusChip
                prefix="Review priority:"
                label={priorityLabel(data.reviewPriority)}
              />
              <StatusChip
                prefix="Assigned reviewer:"
                label={data.assignedReviewerName ?? "Not set"}
              />
              <StatusChip
                tone={
                  data.ageBucket === "waiting_more_than_7_days"
                    ? "warning"
                    : "neutral"
                }
                label={ageBucketLabel(data.ageBucket)}
              />
              {data.dueDateIndicators.map((indicator) => (
                <StatusChip
                  key={indicator}
                  tone="warning"
                  label={dueDateIndicatorLabel(indicator)}
                />
              ))}
            </div>

            <SectionCard title="Workload metrics">
              <WorkloadMetricCards metrics={data.metrics} />
            </SectionCard>

            <SectionCard
              title="Pending reviewer actions"
              description="Each links to the workflow page where human review continues."
            >
              <ReviewerQueueList items={data.queue} showProject={false} />
            </SectionCard>

            <SectionCard
              title="Assignment and review priority"
              description="Reviewer-controlled workflow metadata. Updates require project admin access and are audit attributed. They do not change a project's engineering status."
            >
              <ProjectWorkloadControls
                projectId={projectId}
                currentReviewerName={data.assignedReviewerName}
                currentPriority={data.reviewPriority}
              />
            </SectionCard>

            <div className="flex flex-wrap gap-2">
              <Link href={`${base}/documents`} className="nav-link">
                Documents
              </Link>
              <Link href={`${base}/findings`} className="nav-link">
                Findings
              </Link>
              <Link href={`${base}/evidence-candidates`} className="nav-link">
                Evidence candidate queue
              </Link>
              <Link href={`${base}/checklists`} className="nav-link">
                Checklists
              </Link>
              <Link href={`${base}/response-matrix`} className="nav-link">
                Response matrix
              </Link>
              <Link href={`${base}/resubmittals`} className="nav-link">
                Resubmittal rounds
              </Link>
              <Link href={`${base}/response-packages`} className="nav-link">
                Response packages
              </Link>
            </div>

            <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
              {data.accessNote}
            </p>
          </>
        ) : null}
      </div>
    </div>
  );
}
