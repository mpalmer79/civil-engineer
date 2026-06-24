import type { CadFileUpload } from "@/lib/api";

const statusStyles: Record<string, string> = {
  uploaded: "bg-slate-100 text-slate-600",
  parsed: "bg-water-50 text-water-700",
  parse_failed: "bg-red-50 text-red-700",
  needs_human_review: "bg-amber-50 text-amber-700",
};

// Lists the registered CAD (DXF) files for the project and allows selecting one.
export default function CadFileList({
  files,
  selectedId,
  onSelect,
}: {
  files: CadFileUpload[];
  selectedId: string | null;
  onSelect: (cadFileId: string) => void;
}) {
  if (files.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No CAD files registered yet.
      </div>
    );
  }
  return (
    <div className="surface-card p-4">
      <h3 className="text-sm font-semibold text-slate-800">CAD files</h3>
      <ul className="mt-3 space-y-2">
        {files.map((file) => (
          <li key={file.cadFileId}>
            <button
              type="button"
              onClick={() => onSelect(file.cadFileId)}
              className={`w-full rounded-lg border px-3 py-2 text-left transition-colors ${
                file.cadFileId === selectedId
                  ? "border-water-500 bg-water-50"
                  : "border-slate-200 bg-white hover:bg-slate-50"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-slate-800">
                  {file.fileName}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] ${
                    statusStyles[file.uploadStatus] ?? statusStyles.uploaded
                  }`}
                >
                  {file.uploadStatus.replace(/_/g, " ")}
                </span>
              </div>
              <p className="mt-0.5 text-xs text-slate-500">
                {file.fileType.toUpperCase()} · {file.fileSizeBytes} bytes
              </p>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
