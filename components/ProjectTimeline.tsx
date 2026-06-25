import Link from "next/link";
import type { ProjectTimelineEvent } from "@/lib/api";

// A timeline of meaningful review-support events for the project, newest last.
export default function ProjectTimeline({
  events,
}: {
  events: ProjectTimelineEvent[];
}) {
  if (events.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No timeline events yet.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Project timeline</h3>
      <ol className="mt-4 space-y-3">
        {events.map((event) => (
          <li key={event.timelineEventId} className="flex gap-3">
            <span
              aria-hidden="true"
              className="mt-1 h-2.5 w-2.5 flex-shrink-0 rounded-full bg-water-500"
            />
            <div className="flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Link
                  href={event.targetRoute}
                  className="text-sm font-medium text-slate-800 hover:text-water-700"
                >
                  {event.eventTitle}
                </Link>
                <span className="text-[11px] text-slate-400">
                  {event.sourceModule.replace(/_/g, " ")}
                </span>
              </div>
              <p className="mt-0.5 text-xs text-slate-600">
                {event.eventDescription}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
