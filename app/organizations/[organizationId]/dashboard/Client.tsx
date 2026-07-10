"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
import PermissionDeniedCard from "@/components/PermissionDeniedCard";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import {
  getOrganizationDashboard,
  getOrganizationReviewerWorkload,
  isSignedIn,
  type OrganizationDashboard,
  type OrganizationReviewerWorkloadResult,
} from "@/lib/api";

export default function OrganizationDashboardPageClient({ organizationId }: { organizationId: string }) {
  const [data, setData] = useState<OrganizationDashboard | null>(null);
  const [workload, setWorkload] =
    useState<OrganizationReviewerWorkloadResult | null>(null);
  const [signedIn, setSignedIn] = useState(false);
  const [denied, setDenied] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    const authed = isSignedIn();
    setSignedIn(authed);
    if (!authed) {
      setLoaded(true);
      return;
    }
    getOrganizationDashboard(organizationId).then((result) => {
      if (!active) return;
      if (result.ok && result.data) {
        setData(result.data);
      } else if (result.status === 403) {
        setDenied(true);
      }
      setLoaded(true);
    });
    // Reviewer workload is admin/senior only; a 403 is expected and ignored.
    getOrganizationReviewerWorkload(organizationId).then((result) => {
      if (!active) return;
      if (result.ok && result.data) setWorkload(result.data);
    });
    return () => {
      active = false;
    };
  }, [organizationId]);

  return (
    <div>
      <PageHeader
        eyebrow="Organization dashboard"
        title="Organization workload dashboard"
        description="Cross-project review-support workload for the projects you can access in this organization. Counts are operational indicators only. They do not approve plans, certify compliance, or resolve issues."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <BackendStatusBanner />

        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`/organizations/${organizationId}`}
            className="nav-link"
          >
            Back to organization
          </Link>
        </div>

        {loaded && !signedIn ? (
          <SectionCard title="Sign in required">
            <p className="text-sm text-slate-600">
              <Link href="/login" className="text-water-700 hover:underline">
                Sign in
              </Link>{" "}
              to view this organization dashboard.
            </p>
          </SectionCard>
        ) : null}

        {loaded && signedIn && denied ? (
          <PermissionDeniedCard message="You are not a member of this organization, so its workload dashboard is not available. Ask an organization admin for access." />
        ) : null}

        {data ? (
          <>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <MetricCard
                value={data.projectCount}
                label="Projects"
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

            <SectionCard title="Projects by review-support status">
              {Object.keys(data.statusCounts).length === 0 ? (
                <EmptyState title="No accessible projects in this organization yet" />
              ) : (
                <ul className="flex flex-wrap gap-2">
                  {Object.entries(data.statusCounts).map(([status, count]) => (
                    <li key={status}>
                      <StatusChip label={String(count)} prefix={status} />
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            {workload ? (
              <SectionCard
                title="Reviewer workload summaries"
                description="Workload grouped by assigned reviewer. Visible to organization admins and senior reviewers."
              >
                {workload.reviewers.length === 0 ? (
                  <EmptyState title="No reviewer workload to summarize yet" />
                ) : (
                  <ul className="list-container">
                    {workload.reviewers.map((r) => (
                      <li
                        key={r.assignedReviewerUserId ?? "unassigned"}
                        className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <p className="text-sm font-semibold text-slate-800">
                          {r.assignedReviewerName}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          <StatusChip
                            label={String(r.projectCount)}
                            prefix="projects"
                          />
                          <StatusChip
                            label={String(r.pendingReviewerActionCount)}
                            prefix="pending actions"
                            tone={
                              r.pendingReviewerActionCount > 0
                                ? "warning"
                                : "neutral"
                            }
                          />
                          <StatusChip
                            label={String(r.projectsWithPendingActionCount)}
                            prefix="projects with pending"
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>
            ) : null}

            <SectionCard title="Accessible projects">
              {data.projects.length === 0 ? (
                <EmptyState title="No accessible projects in this organization yet" />
              ) : (
                <ul className="list-container">
                  {data.projects.map((p) => (
                    <li
                      key={p.projectId}
                      className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
                    >
                      <Link
                        href={`/projects/${p.projectId}/workload`}
                        className="font-semibold text-water-700 hover:underline"
                      >
                        {p.projectName}
                      </Link>
                      <StatusChip
                        label={`${p.pendingReviewerActionCount} pending reviewer action${
                          p.pendingReviewerActionCount === 1 ? "" : "s"
                        }`}
                        tone={
                          p.pendingReviewerActionCount > 0 ? "warning" : "neutral"
                        }
                      />
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <p className="alert alert-info">{data.accessNote}</p>
          </>
        ) : null}
      </div>
    </div>
  );
}
