"use client";

import { useState } from "react";

import {
  saveEvidenceCandidate,
  searchProjectEvidence,
  type EvidenceSearchResult,
} from "@/lib/api";

// Reviewer-facing evidence search over indexed PDF page text. Retrieval is
// deterministic and local. There are no live AI calls. Each result is an
// evidence candidate that requires reviewer confirmation, not a conclusion.
type DocumentOption = {
  documentId: string;
  label: string;
  documentType: string | null;
};

const QUERY_TYPES: { value: string; label: string }[] = [
  { value: "keyword", label: "Keyword" },
  { value: "phrase", label: "Exact phrase" },
  { value: "combined", label: "Combined (keyword + filters)" },
];

export default function EvidenceSearchClient({
  projectId,
  documents,
  documentTypes,
}: {
  projectId: string;
  documents: DocumentOption[];
  documentTypes: string[];
}) {
  const [queryText, setQueryText] = useState("");
  const [queryType, setQueryType] = useState("keyword");
  const [documentId, setDocumentId] = useState("");
  const [documentType, setDocumentType] = useState("");
  const [pageMin, setPageMin] = useState("");
  const [pageMax, setPageMax] = useState("");
  const [limit, setLimit] = useState("10");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [results, setResults] = useState<EvidenceSearchResult[] | null>(null);
  const [retrievalQueryId, setRetrievalQueryId] = useState<string | null>(null);
  const [savedKeys, setSavedKeys] = useState<Record<string, string>>({});

  const handleSearch = async () => {
    if (queryText.trim().length < 2) {
      setError("Enter at least two characters to search.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await searchProjectEvidence(projectId, {
      queryText: queryText.trim(),
      queryType,
      filters: {
        documentId: documentId || undefined,
        documentType: documentType || undefined,
        pageMin: pageMin ? Number(pageMin) : undefined,
        pageMax: pageMax ? Number(pageMax) : undefined,
      },
      limit: Number(limit) || 10,
    });
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Search failed.");
      setResults(null);
      return;
    }
    setResults(result.data.results);
    setRetrievalQueryId(result.data.retrievalQueryId);
    setMessage(result.data.message);
    setSavedKeys({});
  };

  const resultKey = (r: EvidenceSearchResult) =>
    `${r.documentId}:${r.pageNumber ?? "x"}`;

  const handleSave = async (
    result: EvidenceSearchResult,
    status: "saved_for_review" | "needs_reviewer_triage",
  ) => {
    const saved = await saveEvidenceCandidate(projectId, {
      documentId: result.documentId,
      documentPageId: result.documentPageId,
      pageNumber: result.pageNumber,
      retrievalQueryId: retrievalQueryId ?? result.retrievalQueryId,
      candidateTitle: `${result.documentName} page ${result.pageNumber ?? "?"}`,
      candidateExcerpt: result.excerpt,
      matchTerms: result.matchTerms,
      rankingScore: result.rankingScore,
      rankingReason: result.rankingReason,
      candidateOrigin: result.candidateOrigin ?? "manual_save",
    });
    if (!saved.ok || !saved.data) {
      setError(saved.error ?? "Could not save the candidate.");
      return;
    }
    setSavedKeys((prev) => ({
      ...prev,
      [resultKey(result)]: saved.data!.candidateStatus,
    }));
  };

  return (
    <div className="space-y-6">
      <div className="surface-card p-6">
        <p className="mb-4 rounded-md bg-water-50 px-3 py-2 text-sm text-water-800">
          Evidence candidates require reviewer confirmation. Retrieval is
          deterministic and local over indexed PDF page text. No live AI is used
          and search results are not conclusions.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Search text
            </label>
            <input
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="detention basin outlet"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Query type
            </label>
            <select
              value={queryType}
              onChange={(e) => setQueryType(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              {QUERY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Result limit
            </label>
            <input
              type="number"
              min={1}
              max={50}
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Document filter
            </label>
            <select
              value={documentId}
              onChange={(e) => setDocumentId(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="">All documents</option>
              {documents.map((d) => (
                <option key={d.documentId} value={d.documentId}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Document type filter
            </label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="">All types</option>
              {documentTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Page from
            </label>
            <input
              type="number"
              min={1}
              value={pageMin}
              onChange={(e) => setPageMin(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Page to
            </label>
            <input
              type="number"
              min={1}
              value={pageMax}
              onChange={(e) => setPageMax(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        {error ? (
          <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <button
          type="button"
          onClick={handleSearch}
          disabled={busy || queryText.trim().length < 2}
          className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Searching..." : "Search indexed evidence"}
        </button>
      </div>

      {message ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {message}
        </p>
      ) : null}

      {results && results.length > 0 ? (
        <ul className="space-y-3">
          {results.map((r) => {
            const key = resultKey(r);
            const savedStatus = savedKeys[key];
            return (
              <li key={key} className="surface-card p-4 text-sm">
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
                  <p className="mt-2 italic text-slate-600">
                    &ldquo;{r.excerpt}&rdquo;
                  </p>
                ) : null}
                {r.matchTerms.length > 0 ? (
                  <p className="mt-1 text-xs text-slate-500">
                    Match terms: {r.matchTerms.join(", ")}
                  </p>
                ) : null}
                {r.rankingReason ? (
                  <p className="mt-1 text-xs text-slate-500">
                    {r.rankingReason}
                  </p>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-2">
                  {savedStatus ? (
                    <span className="rounded-md bg-land-50 px-3 py-1.5 text-xs font-semibold text-land-700">
                      Saved ({savedStatus})
                    </span>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => handleSave(r, "saved_for_review")}
                        className="rounded-md bg-water-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-water-700"
                      >
                        Save candidate
                      </button>
                      <button
                        type="button"
                        onClick={() => handleSave(r, "needs_reviewer_triage")}
                        className="rounded-md border border-water-600 px-3 py-1.5 text-xs font-semibold text-water-700 hover:bg-water-50"
                      >
                        Add to draft queue
                      </button>
                    </>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
