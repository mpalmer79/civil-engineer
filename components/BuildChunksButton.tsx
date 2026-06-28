"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { buildDocumentChunks } from "@/lib/api";

// Builds real-derived chunk evidence from a document's indexed PDF page text.
// Chunking is deterministic and local. It reads indexed page text only. It does
// not OCR, call any AI service, or finalize any review outcome. Re-running is
// idempotent and never removes seeded demo chunks.
export default function BuildChunksButton({
  projectId,
  documentId,
  disabled,
  disabledReason,
}: {
  projectId: string;
  documentId: string;
  disabled?: boolean;
  disabledReason?: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleBuild = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await buildDocumentChunks(projectId, documentId);
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Building page chunks failed.");
      return;
    }
    const data = result.data;
    setMessage(
      `${data.chunkCount} real-derived chunk(s) built from ` +
        `${data.pagesChunked} indexed page(s). These are review-support ` +
        "candidates, not a finding about document content.",
    );
    router.refresh();
  };

  if (disabled) {
    return (
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
        {disabledReason ??
          "Building page chunks requires an indexed PDF document."}
      </p>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleBuild}
        disabled={busy}
        className="rounded-lg border border-water-600 px-4 py-2.5 text-sm font-semibold text-water-700 shadow-sm transition-colors hover:bg-water-50 disabled:opacity-60"
      >
        {busy ? "Building..." : "Build page chunks"}
      </button>
      {message ? (
        <p className="mt-2 rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}
