import type { CadUploadLimits } from "@/lib/api";

// Shows the documented DXF upload limits before a reviewer uploads a file:
// supported file type, size limit, and the review-support boundary. These are
// intake limits, not an engineering determination.
export default function CadUploadLimitsNotice({
  limits,
}: {
  limits: CadUploadLimits | null;
}) {
  if (!limits) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
        Upload limits are unavailable. Start the backend API to see the DXF
        upload limits.
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <p className="text-sm font-semibold text-slate-800">DXF upload limits</p>
      <ul className="mt-2 grid gap-1 text-sm text-slate-600 sm:grid-cols-2">
        <li>
          Supported file type:{" "}
          <span className="font-medium text-slate-800">
            {limits.supportedFileTypes.join(", ").toUpperCase() || "DXF"}
          </span>{" "}
          ({limits.supportedExtensions.join(", ")})
        </li>
        <li>
          Maximum file size:{" "}
          <span className="font-medium text-slate-800">
            {limits.maxFileSizeMb} MB ({limits.maxFileSizeBytes} bytes)
          </span>
        </li>
      </ul>
      <p className="mt-2 text-xs text-slate-500">{limits.note}</p>
    </div>
  );
}
