"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createProjectFinding } from "@/lib/api";

const EVIDENCE_STATUSES = [
  "potential_issue",
  "missing_evidence",
  "conflicting_evidence",
  "unclear_evidence",
  "needs_reviewer_confirmation",
];

const RISK_LEVELS = ["low", "medium", "high"];

// Form to create a reviewer-owned review-support finding. Every finding stays
// under human review and requires human confirmation. It is not a final
// engineering conclusion and never carries approval or compliance language.
export default function ReviewerFindingForm({
  projectId,
}: {
  projectId: string;
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("stormwater");
  const [riskLevel, setRiskLevel] = useState("medium");
  const [evidenceStatus, setEvidenceStatus] = useState("missing_evidence");
  const [evidenceToFind, setEvidenceToFind] = useState("");
  const [reasonItMatters, setReasonItMatters] = useState("");
  const [recommendedHumanAction, setRecommendedHumanAction] = useState("");
  const [relatedDocuments, setRelatedDocuments] = useState("");
  const [reviewerNotes, setReviewerNotes] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    setBusy(true);
    setError(null);
    const result = await createProjectFinding(projectId, {
      title: title.trim(),
      category: category.trim(),
      riskLevel,
      evidenceStatus,
      evidenceToFind: evidenceToFind.trim(),
      reasonItMatters: reasonItMatters.trim(),
      recommendedHumanAction: recommendedHumanAction.trim(),
      relatedDocuments: relatedDocuments
        .split(",")
        .map((d) => d.trim())
        .filter(Boolean),
      reviewerNotes: reviewerNotes.trim(),
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Could not create the finding.");
      return;
    }
    router.push(`/projects/${projectId}/findings`);
  };

  return (
    <div className="surface-card p-6">
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        This is a review-support finding requiring human confirmation. It does
        not approve, certify, verify, resolve, or close anything.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Detention basin outlet detail missing"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Category
          </label>
          <input
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Risk level
          </label>
          <select
            value={riskLevel}
            onChange={(e) => setRiskLevel(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            {RISK_LEVELS.map((r) => (
              <option key={r} value={r}>
                {r}
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
            {EVIDENCE_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Related document IDs (comma separated)
          </label>
          <input
            type="text"
            value={relatedDocuments}
            onChange={(e) => setRelatedDocuments(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
      </div>

      <div className="mt-3">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Evidence to find
        </label>
        <textarea
          value={evidenceToFind}
          onChange={(e) => setEvidenceToFind(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>
      <div className="mt-3">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Reason it matters
        </label>
        <textarea
          value={reasonItMatters}
          onChange={(e) => setReasonItMatters(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>
      <div className="mt-3">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Recommended human action
        </label>
        <textarea
          value={recommendedHumanAction}
          onChange={(e) => setRecommendedHumanAction(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>
      <div className="mt-3">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Reviewer notes
        </label>
        <textarea
          value={reviewerNotes}
          onChange={(e) => setReviewerNotes(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      {error ? (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={busy || !title.trim()}
        className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Creating..." : "Create review-support finding"}
      </button>
    </div>
  );
}
