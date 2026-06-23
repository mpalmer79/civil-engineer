import {
  auditEvents as staticAuditEvents,
  type AuditActorType,
  type AuditEvent,
} from "@/data/auditEvents";

const actorStyles: Record<AuditActorType, string> = {
  system: "bg-water-50 text-water-700 ring-water-600/20",
  reviewer: "bg-land-50 text-land-700 ring-land-600/20",
  evaluator: "bg-indigo-50 text-indigo-700 ring-indigo-600/20",
};

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  });
}

export default function AuditTimeline({
  events = staticAuditEvents,
}: {
  events?: AuditEvent[];
}) {
  return (
    <ol className="relative space-y-6 border-l border-slate-200 pl-6">
      {events.map((event) => (
        <li key={event.auditEventId} className="relative">
          <span
            aria-hidden="true"
            className="absolute -left-[1.95rem] top-1 h-3 w-3 rounded-full border-2 border-white bg-slate-300"
          />
          <div className="surface-card p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-sm font-medium text-slate-900">
                {event.eventType}
              </span>
              <span className={`badge ${actorStyles[event.actorType]}`}>
                {event.actorType}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{event.description}</p>
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
              <span>
                Related entity:{" "}
                <span className="font-mono text-slate-500">
                  {event.relatedEntity}
                </span>
              </span>
              <span>{formatTimestamp(event.timestamp)}</span>
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
