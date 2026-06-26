"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  createDraftFindingFromChecklistItem,
  searchChecklistItemEvidence,
  updateProjectChecklistItem,
  type EvidenceSearchResult,
  type ProjectChecklistItem,
} from "@/lib/api";

// Reviewer controls for one checklist item: update review-support status, add a
// reviewer note, search indexed evidence for the requirement, and create a draft
// finding. Checklist evidence status is review-support only and requires human
// confirmation. Nothing here approves, certifies, or validates anything.

const APPLICABILITY_OPTIONS: { value: string; label: string }[] = [
  { value: "applies", label: "Applies" },
  { value: "not_applicable_by_reviewer", label: "Not applicable by reviewer" },
  { value: "applicability_unclear", label: "Applicability unclear" },
  { value: "needs_reviewer_confirmation", label: "Needs reviewer confirmation" },
];

const EVIDENCE_OPTIONS: { value: string; label: string }[] = [
  { value: "not_reviewed", label: "Not reviewed" },
  { value: "evidence_found", label: "Evidence found" },
  { value: "missing_evidence", label: "Missing evidence" },
  { value: "conflicting_evidence", label: "Conflicting evidence" },
  { value: "unclear_evidence", label: "Unclear evidence" },
  { value: "extraction_unavailable", label: "Extraction unavailable" },
  { value: "needs_reviewer_confirmation", label: "Needs reviewer confirmation" },
];

export default function ChecklistItemReviewPanel({
  projectId,
  item,
}: {
  projectId: string;
  item: ProjectChecklistItem;
}) {
  const router = useRouter();
  const [applicability, setApplicability] = useState(item.applicabilityStatus);
  const [evidenceStatus, setEvidenceStatus] = useState(item.evidenceStatus);
  const [note, setNote] = useState(item.reviewerNote ?? "");
  const [statusBusy, setStatusBusy] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const [searchBusy, setSearchBusy] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchMessage, setSearchMessage] = useState<string | null>(null);
  const [results, setResults] = useState<EvidenceSearchResult[] | null>(null);

  const [draftTitle, setDraftTitle] = useState(
    `${item.itemCode}: ${item.requirementText}`,
  );
  const [draftEvidenceStatus, setDraftEvidenceStatus] = useState(
    "missing_evidence",
  );
  const [draftBusy, setDraftBusy] = useState(false);
  const [draftError, setDraftError] = useState<string | null>(null);
  const [draftFindingId, setDraftFindingId] = useState<string | null>(
    item.relatedFindingId,
  );

  const handleStatusSave = async () => {
    setStatusBusy(true);
    setStatusError(null);
    setStatusMessage(null);
    const result = await updateProjectChecklistItem(
      projectId,
      item.projectChecklistItemId,
      {
        applicabilityStatus: applicability,
        evidenceStatus,
        reviewerNote: note.trim(),
      },
    );
    setStatusBusy(false);
    if (!result.ok) {
      setStatusError(result.error ?? "Could not update the item.");
      return;
    }
    setStatusMessage("Checklist item updated. Status is review-support only.");
    router.refresh();
  };

  const handleSearch = async () => {
    setSearchBusy(true);
    setSearchError(null);
    setSearchMessage(null);
    const result = await searchChecklistItemEvidence(
      projectId,
      item.projectChecklistItemId,
      {},
    );
    setSearchBusy(false);
    if (!result.ok || !result.data) {
      setSearchError(result.error ?? "Search failed.");
      setResults(null);
      return;
    }
    setResults(result.data.results);
    setSearchMessage(result.data.message);
  };

  const handleCreateDraft = async () => {
    if (!draftTitle.trim()) {
      setDraftError("Enter a finding title.");
      return;
    }
    setDraftBusy(true);
    setDraftError(null);
    const result = await createDraftFindingFromChecklistItem(
      projectId,
      item.projectChecklistItemId,
      { title: draftTitle.trim(), evidenceStatus: draftEvidenceStatus },
    );
    setDraftBusy(false);
    if (!result.ok || !result.data) {
      setDraftError(result.error ?? "Could not create the draft finding.");
      return;
    }
    setDraftFindingId(result.data.finding.findingId);
    router.refresh();
  };

  return (
    <div className="space-y-6">
      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Update checklist status
        </h3>
        <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          Checklist evidence status is for review support and requires human
          confirmation.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Applicability
            </label>
            <select
              value={applicability}
              onChange={(e) => setApplicability(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              {APPLICABILITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Evidence status
            </label>
            <select
              value={evidenceStatus}
              onChange={(e) => setEvidenceStatus(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              {EVIDENCE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-3">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Reviewer note
          </label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        {statusError ? (
          <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {statusError}
          </p>
        ) : null}
        {statusMessage ? (
          <p className="mt-3 rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
            {statusMessage}
          </p>
        ) : null}
        <button
          type="button"
          onClick={handleStatusSave}
          disabled={statusBusy}
          className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-water-700 disabled:opacity-60"
        >
          {statusBusy ? "Saving..." : "Save status"}
        </button>
      </div>

      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Search evidence for this requirement
        </h3>
        <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          Deterministic, local search over indexed PDF page text. Results are
          candidates requiring reviewer confirmation, not conclusions.
        </p>
        <button
          type="button"
          onClick={handleSearch}
          disabled={searchBusy}
          className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-water-700 disabled:opacity-60"
        >
          {searchBusy ? "Searching..." : "Search checklist evidence"}
        </button>
        {searchError ? (
          <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {searchError}
          </p>
        ) : null}
        {searchMessage ? (
          <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
            {searchMessage}
          </p>
        ) : null}
        {results && results.length > 0 ? (
          <ul className="mt-3 space-y-2">
            {results.map((r) => (
              <li
                key={`${r.documentId}:${r.pageNumber ?? "x"}`}
                className="rounded-lg border border-slate-200 p-3 text-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold text-slate-800">
                    {r.documentName}
                    {r.pageNumber ? `, page ${r.pageNumber}` : ""}
                  </span>
                  <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                    relevance {r.rankingScore.toFixed(2)}
                  </span>
                </div>
                {r.excerpt ? (
                  <p className="mt-1 italic text-slate-600">
                    &ldquo;{r.excerpt}&rdquo;
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Create draft finding from this item
        </h3>
        <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          This creates a reviewer draft finding. It does not finalize a review
          outcome.
        </p>
        {draftFindingId ? (
          <p className="mt-3 rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
            Draft finding created ({draftFindingId}). It requires human review.
          </p>
        ) : (
          <>
            <div className="mt-4">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Finding title
              </label>
              <input
                type="text"
                value={draftTitle}
                onChange={(e) => setDraftTitle(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div className="mt-3">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Evidence status
              </label>
              <select
                value={draftEvidenceStatus}
                onChange={(e) => setDraftEvidenceStatus(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              >
                {[
                  "missing_evidence",
                  "unclear_evidence",
                  "conflicting_evidence",
                  "needs_reviewer_confirmation",
                  "potential_issue",
                ].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            {draftError ? (
              <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                {draftError}
              </p>
            ) : null}
            <button
              type="button"
              onClick={handleCreateDraft}
              disabled={draftBusy || !draftTitle.trim()}
              className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-water-700 disabled:opacity-60"
            >
              {draftBusy ? "Creating..." : "Create reviewer draft finding"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
