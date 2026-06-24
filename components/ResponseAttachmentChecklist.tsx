import type { ResponsePackageAttachment } from "@/lib/api";

// A read-only attachment checklist for the response package. Each attachment is
// a suggested enclosure for a human reviewer to confirm before any response is
// prepared for issue. The system does not send the attachments.
export default function ResponseAttachmentChecklist({
  attachments,
}: {
  attachments: ResponsePackageAttachment[];
}) {
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Attachment checklist
      </h3>
      {attachments.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">
          No suggested attachments for this draft.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {attachments.map((a) => (
            <li
              key={a.attachmentId}
              className="flex items-start gap-3 rounded-md border border-slate-200 px-3 py-2"
            >
              <span
                aria-hidden="true"
                className={`mt-0.5 text-sm ${
                  a.included ? "text-land-600" : "text-slate-400"
                }`}
              >
                {a.included ? "☑" : "☐"}
              </span>
              <div>
                <p className="text-sm font-medium text-slate-800">{a.label}</p>
                <p className="text-xs text-slate-500">
                  {a.attachmentType.replace(/_/g, " ")}
                  {a.description ? ` · ${a.description}` : ""}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
