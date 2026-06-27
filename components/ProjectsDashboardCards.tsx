"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import MetricCard from "@/components/MetricCard";
import {
  getReviewerDashboard,
  isSignedIn,
  type ReviewerDashboard,
} from "@/lib/api";

// Signed-in summary cards for the projects list. Shows accessible projects,
// projects needing reviewer attention, the package handoff queue, and the
// applicant response review queue. Renders nothing when signed out or when the
// backend is unavailable. Counts are operational indicators only.
export default function ProjectsDashboardCards() {
  const [data, setData] = useState<ReviewerDashboard | null>(null);

  useEffect(() => {
    let active = true;
    if (!isSignedIn()) return;
    getReviewerDashboard().then((result) => {
      if (!active) return;
      if (result.ok && result.data) setData(result.data);
    });
    return () => {
      active = false;
    };
  }, []);

  if (!data) return null;

  return (
    <section className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Your reviewer workload
        </h2>
        <Link href="/dashboard" className="text-sm text-water-700 hover:underline">
          Open reviewer dashboard
        </Link>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          value={data.accessibleProjectCount}
          label="My accessible projects"
          accent="water"
        />
        <MetricCard
          value={data.projectsWithPendingActionCount}
          label="Projects needing reviewer attention"
          accent="amber"
        />
        <MetricCard
          value={data.totals.responsePackagesReadyForHandoff}
          label="Package handoff queue"
          accent="land"
        />
        <MetricCard
          value={data.totals.applicantResponsesNeedingReview}
          label="Applicant response review queue"
          accent="water"
        />
      </div>
    </section>
  );
}
