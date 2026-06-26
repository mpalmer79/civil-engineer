"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createEvidenceCitation } from "@/lib/api";

// Form to create a reviewer-selected, page-level evidence citation for a
// finding. A citation is a reviewer-selected source reference, not proof of
// correctness. It does not approve, certify, verify, or validate anything and
// never changes a finding to a final outcome.
export default function EvidenceCitationForm({
  projectId,
  documentId,
  pageNumber,
  defaultExcerpt,
}: {
  projectId: string;
  documentId: string;
  pageNumber?: number;
  defaultExcerpt?: string;
}) {
  const router = useRouter();
  const [findingId, setFindingId] = useState("");
  const [sectionLabel, setSectionLabel] = useState("");
  const [quotedExcerpt, setQuotedExcerpt] = useState(defaultExcerpt ?? "");
  const [reviewerNote, setReviewerNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!findingId.trim()) {
      setError("Enter the finding ID to cite.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await createEvidenceCitation(projectId, findingId.trim(), {
      documentId,
      pageNumber: pageNumber ?? null,
      sectionLabel: sectionLabel.trim(),
      quotedExcerpt: quotedExcerpt.trim(),
      reviewerNote: reviewerNote.trim(),
    });
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not create the citation.");
      return;
    }
    setMessage(
      `Citation created (${result.data.citationStatus}). It requires reviewer confirmation.`,
    );
    setSectionLabel("");
    setReviewerNote("");
    router.refresh();
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Cite this page as evidence
      </h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        Create a reviewer-selected page-level evidence reference for a finding.
        A citation is a source reference requiring reviewer confirmation, not
        proof of correctness.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Finding ID
          </label>
          <input
            type="text"
            value={findingId}
            onChange={(e) => setFindingId(e.target.value)}
            placeholder="find_user_..."
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Section label (optional)
          </label>
          <input
            type="text"
            value={sectionLabel}
            onChange={(e) => setSectionLabel(e.target.value)}
            placeholder="Outlet detail"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
      </div>
      <div className="mt-3">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Quoted excerpt (optional)
        </label>
        <textarea
          value={quotedExcerpt}
          onChange={(e) => setQuotedExcerpt(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>
      <div className="mt-3">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Reviewer note
        </label>
        <textarea
          value={reviewerNote}
          onChange={(e) => setReviewerNote(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      {error ? (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mt-3 rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
          {message}
        </p>
      ) : null}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={busy || !findingId.trim()}
        className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Creating..." : "Create evidence citation"}
      </button>
    </div>
  );
}
