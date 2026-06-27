"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import EmptyState from "@/components/EmptyState";
import StatusChip, { humanizeStatus } from "@/components/StatusChip";
import ReviewerQueueList from "@/components/ReviewerQueueList";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import { ageBucketLabel } from "@/lib/dashboardLabels";
import { dashboardMedia } from "@/lib/dashboardMedia";
import {
  getReviewerDashboard,
  isSignedIn,
  type ReviewerDashboard,
} from "@/lib/api";

function DashboardMedia({
  src,
  alt,
  className = "",
  imageClassName = "object-contain p-2 sm:p-0 lg:object-cover",
}: {
  src: string;
  alt: string;
  className?: string;
  imageClassName?: string;
}) {
  return (
    <div
      className={`relative w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-card ${className}`}
    >
      <Image
        src={src}
        alt={alt}
        fill
        sizes="(min-width: 1024px) 50vw, (min-width: 640px) 90vw, 100vw"
        className={imageClassName}
      />
    </div>
  );
}

export default function ReviewerDashboardPage() {
  const [data, setData] = useState<ReviewerDashboard | null>(null);
  const [signedIn, setSignedIn] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [backendReachable, setBackendReachable] = useState(true);

  useEffect(() => {
    let active = true;
    const authed = isSignedIn();
    setSignedIn(authed);
    if (!authed) {
      setLoaded(true);
      return;
    }
    getReviewerDashboard().then((result) => {
      if (!active) return;
      setBackendReachable(result.backendReachable);
      if (result.ok && result.data) setData(result.data);
      setLoaded(true);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div>
      <PageHeader
        eyebrow="Reviewer dashboard"
        title="Reviewer workload dashboard"
        description="A visual command center for pending reviewer actions, project workload, queue triage, and operational review-support indicators across the projects you can access."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/dashboard/queue" className="btn btn-primary">
              Open reviewer queue
            </Link>
            <Link href="/projects" className="btn btn-secondary">
              View projects
            </Link>
          </div>
        }
      />

      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:space-y-8 sm:px-6 sm:py-10 lg:px-8">
        <section className="grid gap-5 md:gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <div>
            <span className="chip chip-brand">Reviewer command center</span>
            <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Workload, queue, and handoff visibility
            </h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-600 sm:text-base">
              Use the dashboard to scan active workload, queue items, evidence
              review needs, applicant responses, and packages ready for reviewer
              handoff. Indicators support review, but do not make engineering
              decisions.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link href="/dashboard/queue" className="btn btn-primary">
                Open reviewer queue
              </Link>
              <Link href="/projects" className="btn btn-secondary">
                Browse projects
              </Link>
              <Link href="/start-here" className="btn btn-secondary">
                Start Here
              </Link>
            </div>
          </div>
          <DashboardMedia
            src={dashboardMedia.hero.src}
            alt={dashboardMedia.hero.alt}
            className="h-44 sm:h-60 md:h-72 lg:h-80"
          />
        </section>

        <BackendStatusBanner />

        {loaded && !signedIn ? (
          <section className="surface-card overflow-hidden p-0">
            <div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
              <DashboardMedia
                src={dashboardMedia.emptyState.src}
                alt={dashboardMedia.emptyState.alt}
                className="h-44 rounded-none border-0 shadow-none sm:h-64 lg:h-full"
                imageClassName="object-contain p-2 sm:p-0"
              />
              <div className="p-4 sm:p-6 lg:p-8">
                <EmptyState
                  title="Sign in to view your reviewer dashboard"
                  description="The reviewer dashboard shows workload across the projects you can access. The public Brookside Meadows demo remains available without an account."
                  action={
                    <div className="flex flex-wrap justify-center gap-2">
                      <Link href="/login" className="btn btn-primary">
                        Sign in
                      </Link>
                      <Link href="/register" className="btn btn-secondary">
                        Create account
                      </Link>
                      <Link
                        href="/projects/proj_brookside_meadows"
                        className="btn btn-ghost"
                      >
                        Open Brookside Meadows
                      </Link>
                    </div>
                  }
                />
              </div>
            </div>
          </section>
        ) : null}

        {loaded && signedIn && !data && backendReachable ? (
          <section className="surface-card overflow-hidden p-0">
            <div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
              <DashboardMedia
                src={dashboardMedia.emptyState.src}
                alt={dashboardMedia.emptyState.alt}
                className="h-44 rounded-none border-0 shadow-none sm:h-64 lg:h-full"
                imageClassName="object-contain p-2 sm:p-0"
              />
              <div className="p-4 sm:p-6 lg:p-8">
                <EmptyState
                  title="No accessible real projects yet"
                  description="Create a project record or open the Brookside Meadows demo to explore the review-support workflow."
                  action={
                    <div className="flex flex-wrap justify-center gap-2">
                      <Link href="/projects/new" className="btn btn-primary">
                        Create project record
                      </Link>
                      <Link
                        href="/projects/proj_brookside_meadows"
                        className="btn btn-secondary"
                      >
                        Open Brookside Meadows
                      </Link>
                    </div>
                  }
                />
              </div>
            </div>
          </section>
        ) : null}

        {loaded && signedIn && !backendReachable ? (
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Dashboard data is served by the backend. Start the API to view your
              reviewer workload.
            </p>
          </SectionCard>
        ) : null}

        {data ? (
          <>
            <section className="grid gap-5 md:gap-6 lg:grid-cols-[1fr_0.95fr] lg:items-center">
              <div className="space-y-3 sm:space-y-4">
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <MetricCard
                    value={data.accessibleProjectCount}
                    label="Accessible projects"
                    accent="water"
                  />
                  <MetricCard
                    value={data.projectsWithPendingActionCount}
                    label="Projects needing reviewer attention"
                    accent="amber"
                  />
                  <MetricCard
                    value={data.totals.pendingReviewerActionCount}
                    label="Pending reviewer actions"
                    accent="amber"
                  />
                  <MetricCard
                    value={data.totals.responsePackagesReadyForHandoff}
                    label="Packages ready for reviewer handoff"
                    accent="land"
                  />
                </div>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <MetricCard
                    value={data.totals.documentsNeedingIndexing}
                    label="Documents needing indexing"
                    accent="water"
                  />
                  <MetricCard
                    value={data.totals.evidenceCandidatesNeedingTriage}
                    label="Evidence candidates needing triage"
                    accent="water"
                  />
                  <MetricCard
                    value={
                      data.totals.checklistItemsMissingEvidence +
                      data.totals.checklistItemsUnclearEvidence
                    }
                    label="Checklist items needing evidence review"
                    accent="amber"
                  />
                  <MetricCard
                    value={data.totals.applicantResponsesNeedingReview}
                    label="Applicant responses needing reviewer review"
                    accent="water"
                  />
                </div>
              </div>

              <DashboardMedia
                src={dashboardMedia.workloadMetrics.src}
                alt={dashboardMedia.workloadMetrics.alt}
                className="hidden h-56 md:block lg:h-72"
                imageClassName="object-contain p-3"
              />
            </section>

            <section className="grid gap-5 md:gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
              <DashboardMedia
                src={dashboardMedia.queue.src}
                alt={dashboardMedia.queue.alt}
                className="h-48 sm:h-64 lg:h-80"
                imageClassName="object-contain p-2 sm:p-3"
              />
              <SectionCard
                title="Reviewer queue"
                description="Pending reviewer actions across your accessible projects. Each links to the project workflow page where human review continues."
              >
                <ReviewerQueueList items={data.queue.slice(0, 12)} />
                <div className="mt-4">
                  <Link href="/dashboard/queue" className="btn btn-primary btn-sm">
                    Open full reviewer queue
                  </Link>
                </div>
              </SectionCard>
            </section>

            <section className="grid gap-5 md:gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
              <SectionCard
                title="Accessible projects"
                description="Projects you can access, ordered by pending reviewer action."
              >
                {data.projects.length === 0 ? (
                  <EmptyState
                    title="No accessible real projects yet"
                    description="Create a real project record or open the public Brookside Meadows demo to explore the review-support workflow."
                    action={
                      <Link href="/projects/new" className="btn btn-primary btn-sm">
                        Create project record
                      </Link>
                    }
                  />
                ) : (
                  <div className="list-container">
                    {data.projects.map((p) => (
                      <div
                        key={p.projectId}
                        className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0">
                          <Link
                            href={`/projects/${p.projectId}`}
                            className="break-words text-sm font-semibold text-water-700 hover:underline"
                          >
                            {p.projectName}
                          </Link>
                          <div className="mt-1 flex flex-wrap items-center gap-2">
                            <StatusChip
                              prefix="Status:"
                              label={humanizeStatus(p.status)}
                            />
                            <StatusChip
                              tone={
                                p.ageBucket === "waiting_more_than_7_days"
                                  ? "warning"
                                  : "neutral"
                              }
                              label={ageBucketLabel(p.ageBucket)}
                            />
                          </div>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <StatusChip
                            tone={
                              p.pendingReviewerActionCount > 0
                                ? "warning"
                                : "neutral"
                            }
                            label={`${p.pendingReviewerActionCount} pending reviewer action${
                              p.pendingReviewerActionCount === 1 ? "" : "s"
                            }`}
                          />
                          <Link
                            href={`/projects/${p.projectId}/workload`}
                            className="btn btn-secondary btn-sm"
                          >
                            Workload
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>

              <div className="space-y-4">
                <DashboardMedia
                  src={dashboardMedia.mobilePreview.src}
                  alt={dashboardMedia.mobilePreview.alt}
                  className="hidden h-72 sm:block lg:h-80"
                  imageClassName="object-contain p-3"
                />
                <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
                  {data.accessNote}
                </p>
              </div>
            </section>
          </>
        ) : null}

        <SafetyBoundaryBanner variant="compact" />
      </div>
    </div>
  );
}
