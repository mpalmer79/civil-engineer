"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { promoteCandidateToDraftFinding } from "@/lib/api";

// Promote an evidence candidate into a reviewer draft finding. The reviewer
// confirms or edits every field. The risk level is reviewer-entered, never a
// system conclusion. This creates a reviewer draft finding; it does not
// finalize a review outcome.
const EVIDENCE_STATUSES = [
  "needs_reviewer_confirmation",
  "potential_issue",
  "missing_evidence",
  "conflicting_evidence",
  "unclear_evidence",
];

const RISK_LEVELS = ["low", "medium", "high"];

export default function PromoteCandidateForm({
  projectId,
  candidateId,
  defaultTitle,
  defaultExcerpt,
  alreadyPromoted,
  promotedFindingId,
}: {
  projectId: string;
  candidateId: string;
  defaultTitle: string;
  defaultExcerpt: string | null;
  alreadyPromoted: boolean;
  promotedFindingId: string | null;
}) {
  const router = useRouter();
  const [title, setTitle] = useState(defaultTitle);
  const [category, setCategory] = useState("stormwater");
  const [riskLevel, setRiskLevel] = useState("medium");
  const [evidenceStatus, setEvidenceStatus] = useState(
    "needs_reviewer_confirmation",
  );
  const [evidenceToFind, setEvidenceToFind] = useState("");
  const [reasonItMatters, setReasonItMatters] = useState("");
  const [recommendedHumanAction, setRecommendedHumanAction] = useState("");
  const [reviewerNote, setReviewerNote] = useState("");
  const [citationExcerpt, setCitationExcerpt] = useState(defaultExcerpt ?? "");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [findingId, setFindingId] = useState<string | null>(null);

  if (alreadyPromoted) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Promoted to draft finding
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          This candidate was promoted into reviewer draft finding{" "}
          <code className="rounded bg-slate-100 px-1">{promotedFindingId}</code>
          . It remains under human review and is not a final outcome.
        </p>
      </div>
    );
  }

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError("Enter a finding title.");
      return;
    }
    setBusy(true);
    setError(null);
    const result = await promoteCandidateToDraftFinding(projectId, candidateId, {
      title: title.trim(),
      category: category.trim(),
      riskLevel,
      evidenceStatus,
      evidenceToFind: evidenceToFind.trim(),
      reasonItMatters: reasonItMatters.trim(),
      recommendedHumanAction: recommendedHumanAction.trim(),
      reviewerNote: reviewerNote.trim(),
      citationExcerpt: citationExcerpt.trim(),
    });
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not promote the candidate.");
      return;
    }
    setFindingId(result.data.finding.findingId);
    router.refresh();
  };

  if (findingId) {
    return (
      <div className="surface-card p-6">
        <p className="rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
          Reviewer draft finding created ({findingId}). It requires human review
          and does not finalize a review outcome.
        </p>
      </div>
    );
  }

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Promote to reviewer draft finding
      </h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        This creates a reviewer draft finding. It does not finalize a review
        outcome. Confirm or edit each field. The risk level is reviewer-entered.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Finding title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
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
            Risk level (reviewer-entered)
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
        <div className="sm:col-span-2">
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
        <div className="sm:col-span-2">
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
        <div className="sm:col-span-2">
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
        <div className="sm:col-span-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Citation excerpt or page reference
          </label>
          <textarea
            value={citationExcerpt}
            onChange={(e) => setCitationExcerpt(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div className="sm:col-span-2">
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
        {busy ? "Creating draft finding..." : "Create reviewer draft finding"}
      </button>
    </div>
  );
}
