"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
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
          <SectionCard title="Sign in to view your reviewer queue">
            <p className="text-sm text-slate-600">
              <Link href="/login" className="text-water-700 hover:underline">
                Sign in
              </Link>{" "}
              to view pending reviewer actions across your accessible projects.
            </p>
          </SectionCard>
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
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
                The reviewer queue is served by the backend. Start the API to
                view it.
              </p>
            )}
          </SectionCard>
        ) : null}
      </div>
    </div>
  );
}
