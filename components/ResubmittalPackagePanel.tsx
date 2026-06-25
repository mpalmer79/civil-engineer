"use client";

import type { CadFileUpload, ResubmittalPackage } from "@/lib/api";

const RESUBMITTAL_STATUSES = [
  "received",
  "intake_review",
  "needs_more_information",
  "ready_for_comparison",
  "comparison_complete",
  "reviewer_checked",
  "archived",
];

// Shows resubmittal packages with their linked documents and lets a reviewer
// update status and link an uploaded DXF file.
export default function ResubmittalPackagePanel({
  packages,
  cadFiles,
  selectedId,
  onSelect,
  onStatusChange,
  onLinkCadFile,
}: {
  packages: ResubmittalPackage[];
  cadFiles: CadFileUpload[];
  selectedId: string | null;
  onSelect: (resubmittalPackageId: string) => void;
  onStatusChange: (resubmittalPackageId: string, status: string) => void;
  onLinkCadFile: (resubmittalPackageId: string, cadFileId: string) => void;
}) {
  if (packages.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No resubmittal packages yet. Record one to start a review round.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Resubmittal packages
      </h3>
      <ul className="mt-4 space-y-3">
        {packages.map((pkg) => {
          const selected = pkg.resubmittalPackageId === selectedId;
          return (
            <li
              key={pkg.resubmittalPackageId}
              className={`rounded-lg border px-3 py-3 ${
                selected
                  ? "border-water-500 bg-water-50"
                  : "border-slate-200 bg-white"
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => onSelect(pkg.resubmittalPackageId)}
                  className="text-sm font-semibold text-water-700 hover:text-water-600"
                >
                  {pkg.packageName}
                </button>
                <span className="text-[11px] text-slate-500">
                  from {pkg.submittedBy}
                </span>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <label className="text-xs text-slate-500">Status</label>
                <select
                  value={pkg.status}
                  onChange={(e) =>
                    onStatusChange(pkg.resubmittalPackageId, e.target.value)
                  }
                  className="rounded-md border border-slate-300 px-2 py-1 text-xs"
                >
                  {RESUBMITTAL_STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
                {cadFiles.length > 0 ? (
                  <select
                    defaultValue=""
                    onChange={(e) => {
                      if (e.target.value) {
                        onLinkCadFile(pkg.resubmittalPackageId, e.target.value);
                        e.target.value = "";
                      }
                    }}
                    className="rounded-md border border-slate-300 px-2 py-1 text-xs"
                  >
                    <option value="">Link DXF file...</option>
                    {cadFiles.map((f) => (
                      <option key={f.cadFileId} value={f.cadFileId}>
                        {f.originalFileName || f.fileName}
                      </option>
                    ))}
                  </select>
                ) : null}
              </div>
              {pkg.documents && pkg.documents.length > 0 ? (
                <ul className="mt-2 space-y-1">
                  {pkg.documents.map((doc) => (
                    <li
                      key={doc.resubmittalDocumentId}
                      className="text-xs text-slate-600"
                    >
                      <span className="font-medium">
                        {doc.documentType.replace(/_/g, " ")}
                      </span>
                      {doc.fileName ? ` · ${doc.fileName}` : ""}
                    </li>
                  ))}
                </ul>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
