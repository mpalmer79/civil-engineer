import type { WorkflowItemDetail } from "@/lib/api";
import WorkflowStatusBadge from "@/components/WorkflowStatusBadge";

// Detail view for a selected workflow item: its description, source, evidence
// links, and open follow-up requests. This organizes review-support evidence
// for a human reviewer and does not state a final engineering decision.
export default function WorkflowItemDetailPanel({
  item,
}: {
  item: WorkflowItemDetail | null;
}) {
  if (!item) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Select a workflow item to see its details and evidence.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">{item.title}</h3>
        <WorkflowStatusBadge status={item.status} />
      </div>
      <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
        <span>severity: {item.severity}</span>
        <span aria-hidden="true">·</span>
        <span>section: {item.sectionType.replace(/_/g, " ")}</span>
        <span aria-hidden="true">·</span>
        <span>assigned: {item.assignedRole.replace(/_/g, " ")}</span>
        {item.targetDate ? (
          <>
            <span aria-hidden="true">·</span>
            <span>target: {item.targetDate}</span>
          </>
        ) : null}
      </div>
      <p className="mt-3 text-sm text-slate-600">{item.description}</p>

      {item.reviewerNote ? (
        <div className="mt-4 rounded-lg bg-slate-50 px-3 py-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Latest reviewer note
          </p>
          <p className="mt-1 text-sm text-slate-700">{item.reviewerNote}</p>
        </div>
      ) : null}

      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Evidence links ({item.evidenceLinks.length})
        </p>
        {item.evidenceLinks.length === 0 ? (
          <p className="mt-1 text-sm text-slate-500">
            No linked source evidence for this item.
          </p>
        ) : (
          <ul className="mt-2 space-y-1.5">
            {item.evidenceLinks.map((link) => (
              <li
                key={link.evidenceLinkId}
                className="rounded-md border border-slate-200 px-3 py-2 text-sm"
              >
                <span className="font-medium text-slate-700">{link.label}</span>
                <span className="ml-2 text-xs text-slate-500">
                  {link.evidenceType.replace(/_/g, " ")} ·{" "}
                  {link.relationship.replace(/_/g, " ")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {item.followUps.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Follow-up requests ({item.followUps.length})
          </p>
          <ul className="mt-2 space-y-1.5">
            {item.followUps.map((f) => (
              <li
                key={f.followUpId}
                className="rounded-md border border-slate-200 px-3 py-2 text-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium text-slate-700">
                    From {f.requestedFrom}
                  </span>
                  <span className="badge bg-amber-50 text-amber-700 ring-amber-600/20">
                    {f.status.replace(/_/g, " ")}
                  </span>
                </div>
                <p className="mt-1 text-slate-600">{f.requestReason}</p>
                <p className="mt-1 text-xs text-slate-500">
                  Requested: {f.requestedInformation}
                  {f.targetDate ? ` · target ${f.targetDate}` : ""}
                </p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
