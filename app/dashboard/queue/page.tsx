"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import EmptyState from "@/components/EmptyState";
import ReviewerQueueList from "@/components/ReviewerQueueList";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import { QUEUE_ITEM_TYPE_LABELS } from "@/lib/dashboardLabels";
import { getReviewerQueue, isSignedIn, type ReviewerQueue } from "@/lib/api";

const FILTERS: { value: string; label: string }[] = [
  { value: "", label: "All actions" },
  ...Object.entries(QUEUE_ITEM_TYPE_LABELS).map(([value, label]) => ({
    value,
    label,
  })),
];

export default function ReviewerQueuePage() {
  const [data, setData] = useState<ReviewerQueue | null>(null);
  const [signedIn, setSignedIn] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    let active = true;
    const authed = isSignedIn();
    setSignedIn(authed);
    if (!authed) {
      setLoaded(true);
      return;
    }
    getReviewerQueue(filter ? { itemType: filter } : undefined).then(
      (result) => {
        if (!active) return;
        if (result.ok && result.data) setData(result.data);
        else setData(null);
        setLoaded(true);
      },
    );
    return () => {
      active = false;
    };
  }, [filter]);

  return (
    <div>
      <PageHeader
        eyebrow="Reviewer queue"
        title="Reviewer queue"
        description="Pending reviewer actions across the projects you can access, with safe aging indicators. Each item links to the project workflow page where human review continues. The queue is an operational helper, not a final review outcome."
      />

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <BackendStatusBanner />

        <div className="flex flex-wrap items-center gap-3">
          <Link href="/dashboard" className="nav-link">
            Back to dashboard
          </Link>
        </div>

        {loaded && !signedIn ? (
          <EmptyState
            title="Sign in to view your reviewer queue"
            description="The reviewer queue lists pending reviewer actions across the projects you can access. The public Brookside Meadows demo remains available without an account."
            action={
              <>
                <Link href="/login" className="btn btn-primary btn-sm">
                  Sign in
                </Link>
                <Link href="/register" className="btn btn-secondary btn-sm">
                  Create an account
                </Link>
              </>
            }
          />
        ) : null}

        {signedIn ? (
          <SectionCard title="Filter the queue">
            <div className="flex flex-wrap gap-2">
              {FILTERS.map((f) => (
                <button
                  key={f.value || "all"}
                  type="button"
                  onClick={() => setFilter(f.value)}
                  className={`rounded-md px-3 py-1.5 text-xs font-semibold ring-1 ${
                    filter === f.value
                      ? "bg-water-600 text-white ring-water-600"
                      : "bg-white text-slate-600 ring-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </SectionCard>
        ) : null}

        {signedIn ? (
          <SectionCard
            title="Queue items"
            description={
              data ? `${data.itemCount} pending reviewer action group(s)` : undefined
            }
          >
            {data ? (
              <ReviewerQueueList items={data.items} />
            ) : (
              <div className="alert alert-warning" role="alert">
                The reviewer queue is served by the backend. Start the API to
                view it. No data is hidden when the backend is unavailable.
              </div>
            )}
          </SectionCard>
        ) : null}
      </div>
    </div>
  );
}
