import type { ResponsePackageItem } from "@/lib/api";

// Shows the traceability behind a response item: its linked workflow item,
// packet item, source type and id, and the source evidence links. This is
// review-support traceability, not a verification of the evidence.
export default function ResponseEvidencePanel({
  item,
}: {
  item: ResponsePackageItem | null;
}) {
  if (!item) {
    return null;
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Linked evidence</h3>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <dt className="text-slate-500">Source type</dt>
        <dd className="text-slate-700">{item.sourceType.replace(/_/g, " ")}</dd>
        <dt className="text-slate-500">Source id</dt>
        <dd className="break-all text-slate-700">{item.sourceId ?? "n/a"}</dd>
        <dt className="text-slate-500">Workflow item</dt>
        <dd className="break-all text-slate-700">
          {item.workflowItemId ?? "n/a"}
        </dd>
        <dt className="text-slate-500">Packet item</dt>
        <dd className="break-all text-slate-700">
          {item.packetItemId ?? "n/a"}
        </dd>
      </dl>

      <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
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
  );
}
