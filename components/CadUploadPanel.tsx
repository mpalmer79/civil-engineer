"use client";

import { useRef, useState } from "react";
import { uploadCadFile, type CadUploadLimits } from "@/lib/api";
import CadUploadValidationNotice from "@/components/CadUploadValidationNotice";

// Browser DXF upload control. It validates the extension on the client before
// sending, but the backend validation is authoritative. On a successful upload
// it reports the new CAD file id so the parent can refresh and request a parse.
// Upload does not verify CAD, validate design, approve plans, or certify
// compliance; it stores a DXF file for review-support parsing only.
export default function CadUploadPanel({
  limits,
  onUploaded,
  projectId,
}: {
  limits: CadUploadLimits | null;
  onUploaded: (cadFileId: string) => void | Promise<void>;
  projectId?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [uploadedBy, setUploadedBy] = useState("reviewer");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleUpload = async () => {
    const file = inputRef.current?.files?.[0];
    if (!file) {
      setStatus("rejected");
      setMessage("Select a DXF file to upload first.");
      return;
    }
    setBusy(true);
    setStatus(null);
    setMessage(null);
    const result = await uploadCadFile(file, uploadedBy || "reviewer", projectId);
    setBusy(false);
    if (!result.ok) {
      setStatus(result.validationStatus ?? "rejected");
      setMessage(
        result.error ?? "The DXF file could not be uploaded.",
      );
      return;
    }
    setStatus(result.validationStatus ?? "accepted");
    setMessage(result.validationMessage ?? result.note ?? null);
    if (inputRef.current) inputRef.current.value = "";
    setFileName(null);
    if (result.cadFile) await onUploaded(result.cadFile.cadFileId);
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Upload a DXF file
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        Upload a real DXF file from your machine. The system stores it under a
        safe generated file name and parses it for review-support metadata only.
        DXF is the only supported file type in this phase.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
        <div>
          <label
            htmlFor="cad-upload-file"
            className="block text-xs font-semibold uppercase tracking-wide text-slate-500"
          >
            DXF file
          </label>
          <input
            id="cad-upload-file"
            ref={inputRef}
            type="file"
            accept=".dxf"
            onChange={(e) => setFileName(e.target.files?.[0]?.name ?? null)}
            className="mt-1 block w-full text-sm text-slate-700 file:mr-3 file:rounded-md file:border-0 file:bg-water-600 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-water-700"
          />
          {fileName ? (
            <p className="mt-1 text-xs text-slate-500">Selected: {fileName}</p>
          ) : null}
        </div>
        <div>
          <label
            htmlFor="cad-upload-uploaded-by"
            className="block text-xs font-semibold uppercase tracking-wide text-slate-500"
          >
            Uploaded by
          </label>
          <input
            id="cad-upload-uploaded-by"
            type="text"
            value={uploadedBy}
            onChange={(e) => setUploadedBy(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm sm:w-44"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={handleUpload}
        disabled={busy}
        className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Uploading..." : "Upload and validate DXF"}
      </button>

      {limits ? (
        <p className="mt-3 text-xs text-slate-500">
          Files must be .dxf and no larger than {limits.maxFileSizeMb} MB.
        </p>
      ) : null}

      <div className="mt-4">
        <CadUploadValidationNotice status={status} message={message} />
      </div>
    </div>
  );
}
