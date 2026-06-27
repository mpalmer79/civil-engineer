"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import PermissionDeniedCard from "@/components/PermissionDeniedCard";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import {
  getOrganizationDashboard,
  getOrganizationReviewerWorkload,
  isSignedIn,
  type OrganizationDashboard,
  type OrganizationReviewerWorkloadResult,
} from "@/lib/api";

export default function OrganizationDashboardPage({
  params,
}: {
  params: { organizationId: string };
}) {
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
    getOrganizationDashboard(params.organizationId).then((result) => {
      if (!active) return;
      if (result.ok && result.data) {
        setData(result.data);
      } else if (result.status === 403) {
        setDenied(true);
      }
      setLoaded(true);
    });
    // Reviewer workload is admin/senior only; a 403 is expected and ignored.
    getOrganizationReviewerWorkload(params.organizationId).then((result) => {
      if (!active) return;
      if (result.ok && result.data) setWorkload(result.data);
    });
    return () => {
      active = false;
    };
  }, [params.organizationId]);

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
            href={`/organizations/${params.organizationId}`}
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
                <p className="text-sm text-slate-600">
                  No accessible projects in this organization yet.
                </p>
              ) : (
                <ul className="flex flex-wrap gap-2">
                  {Object.entries(data.statusCounts).map(([status, count]) => (
                    <li
                      key={status}
                      className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200"
                    >
                      {status}: {count}
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
                  <p className="text-sm text-slate-600">
                    No reviewer workload to summarize yet.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                          <th className="px-3 py-2">Assigned reviewer</th>
                          <th className="px-3 py-2">Projects</th>
                          <th className="px-3 py-2">Pending actions</th>
                          <th className="px-3 py-2">Projects with pending</th>
                        </tr>
                      </thead>
                      <tbody>
                        {workload.reviewers.map((r) => (
                          <tr
                            key={r.assignedReviewerUserId ?? "unassigned"}
                            className="border-b border-slate-100"
                          >
                            <td className="px-3 py-2 text-slate-800">
                              {r.assignedReviewerName}
                            </td>
                            <td className="px-3 py-2 text-slate-600">
                              {r.projectCount}
                            </td>
                            <td className="px-3 py-2 text-slate-600">
                              {r.pendingReviewerActionCount}
                            </td>
                            <td className="px-3 py-2 text-slate-600">
                              {r.projectsWithPendingActionCount}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </SectionCard>
            ) : null}

            <SectionCard title="Accessible projects">
              {data.projects.length === 0 ? (
                <p className="text-sm text-slate-600">
                  No accessible projects in this organization yet.
                </p>
              ) : (
                <ul className="space-y-2">
                  {data.projects.map((p) => (
                    <li
                      key={p.projectId}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 p-3 text-sm"
                    >
                      <Link
                        href={`/projects/${p.projectId}/workload`}
                        className="font-semibold text-water-700 hover:underline"
                      >
                        {p.projectName}
                      </Link>
                      <span className="badge bg-amber-50 text-amber-700 ring-1 ring-amber-200">
                        {p.pendingReviewerActionCount} pending reviewer action
                        {p.pendingReviewerActionCount === 1 ? "" : "s"}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
              {data.accessNote}
            </p>
          </>
        ) : null}
      </div>
    </div>
  );
}
