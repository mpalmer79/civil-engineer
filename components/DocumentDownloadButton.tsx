"use client";

import { useState } from "react";

import { downloadDocument } from "@/lib/api";

// Download a stored document through the access-controlled backend route. The
// Authorization header is attached automatically. The file is streamed from the
// storage provider; the storage key and any signed URL stay on the backend.
export default function DocumentDownloadButton({
  projectId,
  documentId,
  fileName,
  available,
}: {
  projectId: string;
  documentId: string;
  fileName: string;
  available: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!available) {
    return (
      <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
        The file is not available in storage. Upload or re-upload a file to make
        it retrieval ready.
      </p>
    );
  }

  const handleDownload = async () => {
    setBusy(true);
    setError(null);
    const result = await downloadDocument(projectId, documentId, fileName);
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Download failed.");
    }
  };

  return (
    <div>
      <button
        type="button"
        onClick={handleDownload}
        disabled={busy}
        className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Preparing download..." : "Download file"}
      </button>
      {error ? (
        <p className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}
