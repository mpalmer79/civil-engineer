"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import ReviewerQueueList from "@/components/ReviewerQueueList";
import {
  getProjectPendingActions,
  type ProjectPendingActions,
} from "@/lib/api";

// Project overview workload card. Shows the pending reviewer action count and a
// short pending-action list with a link to the full project workload page.
// Counts are operational indicators only; they do not represent approval,
// compliance, or issue resolution.
export default function ProjectWorkloadCard({
  projectId,
}: {
  projectId: string;
}) {
  const [data, setData] = useState<ProjectPendingActions | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    getProjectPendingActions(projectId).then((result) => {
      if (!active) return;
      if (result.ok && result.data) setData(result.data);
      setLoaded(true);
    });
    return () => {
      active = false;
    };
  }, [projectId]);

  if (!loaded) {
    return (
      <div className="surface-card p-6">
        <p className="text-sm text-slate-500">Loading workload summary...</p>
      </div>
    );
  }

  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-900">
          Workload and pending actions
        </h2>
        <Link
          href={`/projects/${projectId}/workload`}
          className="text-sm text-water-700 hover:underline"
        >
          Open project workload
        </Link>
      </div>
      {data ? (
        <>
          <p className="mt-2 text-sm text-slate-600">
            {data.pendingReviewerActionCount} pending reviewer action
            {data.pendingReviewerActionCount === 1 ? "" : "s"} listed for this
            project.
          </p>
          <div className="mt-4">
            <ReviewerQueueList items={data.items.slice(0, 6)} showProject={false} />
          </div>
        </>
      ) : (
        <p className="mt-2 text-sm text-slate-500">
          Workload data is served by the backend. Start the API to view pending
          reviewer actions.
        </p>
      )}
    </div>
  );
}
