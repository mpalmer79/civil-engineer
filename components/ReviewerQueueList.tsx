import Link from "next/link";

import { ageBucketLabel, queueTypeLabel } from "@/lib/dashboardLabels";
import type { ReviewerQueueItem } from "@/lib/api";

// Presentational reviewer queue list. Each item is a pending reviewer action
// across accessible projects and links to the project workflow page where human
// review continues. Counts are operational indicators, not final outcomes.
export default function ReviewerQueueList({
  items,
  showProject = true,
  emptyMessage = "No pending reviewer actions are currently listed for your accessible projects.",
}: {
  items: ReviewerQueueItem[];
  showProject?: boolean;
  emptyMessage?: string;
}) {
  if (items.length === 0) {
    return (
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
        {emptyMessage}
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.queueItemId}
          className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 p-3"
        >
          <div className="min-w-0">
            <Link
              href={item.targetPath}
              className="text-sm font-semibold text-water-700 hover:underline"
            >
              {queueTypeLabel(item.itemType)}
            </Link>
            {showProject ? (
              <p className="text-xs text-slate-500">{item.projectName}</p>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <span className="badge bg-amber-50 text-amber-700 ring-1 ring-amber-200">
              {item.count} pending reviewer action
              {item.count === 1 ? "" : "s"}
            </span>
            <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
              {ageBucketLabel(item.ageBucket)}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
