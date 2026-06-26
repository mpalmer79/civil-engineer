"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { indexPdfDocument } from "@/lib/api";

// Triggers deterministic PDF page indexing for an uploaded PDF document.
// Indexing extracts embedded text only. It does not OCR, call any AI service,
// approve, certify, verify, or validate anything.
export default function IndexPdfButton({
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

  const handleIndex = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await indexPdfDocument(projectId, documentId);
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Indexing failed.");
      return;
    }
    setMessage(result.data.summary);
    router.refresh();
  };

  if (disabled) {
    return (
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
        {disabledReason ?? "PDF indexing requires an uploaded PDF file."}
      </p>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleIndex}
        disabled={busy}
        className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Indexing..." : "Index PDF pages"}
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
