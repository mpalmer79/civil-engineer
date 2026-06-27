"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import ReviewerQueueList from "@/components/ReviewerQueueList";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import {
  getReviewerDashboard,
  isSignedIn,
  type ReviewerDashboard,
} from "@/lib/api";

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
        description="A cross-project view of pending reviewer actions and operational review-support metrics across the projects you can access. Counts are operational indicators only. They do not approve plans, certify compliance, resolve issues, or make final engineering decisions."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <BackendStatusBanner />

        {loaded && !signedIn ? (
          <SectionCard title="Sign in to view your reviewer dashboard">
            <p className="text-sm text-slate-600">
              The reviewer dashboard shows workload across the projects you can
              access.{" "}
              <Link href="/login" className="text-water-700 hover:underline">
                Sign in
              </Link>{" "}
              or{" "}
              <Link href="/register" className="text-water-700 hover:underline">
                create an account
              </Link>{" "}
              to continue. The public{" "}
              <Link
                href="/projects/proj_brookside_meadows"
                className="text-water-700 hover:underline"
              >
                Brookside Meadows demo
              </Link>{" "}
              remains available without an account.
            </p>
          </SectionCard>
        ) : null}

        {loaded && signedIn && !data && backendReachable ? (
          <SectionCard title="No accessible real projects yet">
            <p className="text-sm text-slate-600">
              No accessible real projects yet. Create a project or open the{" "}
              <Link
                href="/projects/proj_brookside_meadows"
                className="text-water-700 hover:underline"
              >
                Brookside Meadows demo
              </Link>
              .
            </p>
          </SectionCard>
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
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
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

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
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

            <SectionCard
              title="Reviewer queue"
              description="Pending reviewer actions across your accessible projects. Each links to the project workflow page where human review continues."
            >
              <ReviewerQueueList items={data.queue.slice(0, 12)} />
              <div className="mt-4">
                <Link href="/dashboard/queue" className="nav-link">
                  Open full reviewer queue
                </Link>
              </div>
            </SectionCard>

            <SectionCard
              title="Accessible projects"
              description="Projects you can access, ordered by pending reviewer action."
            >
              {data.projects.length === 0 ? (
                <p className="text-sm text-slate-600">
                  No accessible real projects yet.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                        <th className="px-3 py-2">Project</th>
                        <th className="px-3 py-2">Status</th>
                        <th className="px-3 py-2">Pending actions</th>
                        <th className="px-3 py-2">Waiting</th>
                        <th className="px-3 py-2">Workload</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.projects.map((p) => (
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
                          <td className="px-3 py-2 text-slate-600">{p.status}</td>
                          <td className="px-3 py-2 text-slate-600">
                            {p.pendingReviewerActionCount}
                          </td>
                          <td className="px-3 py-2 text-slate-600">
                            {p.ageBucket.replaceAll("_", " ")}
                          </td>
                          <td className="px-3 py-2">
                            <Link
                              href={`/projects/${p.projectId}/workload`}
                              className="text-water-700 hover:underline"
                            >
                              Workload
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>

            <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
              {data.accessNote}
            </p>
          </>
        ) : null}

        <SafetyBoundaryBanner variant="compact" />
      </div>
    </div>
  );
}
