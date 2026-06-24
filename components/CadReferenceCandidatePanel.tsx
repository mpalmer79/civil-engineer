import type { CadReferenceCandidate } from "@/lib/api";

const confidenceStyles: Record<string, string> = {
  high: "bg-land-50 text-land-700",
  medium: "bg-slate-100 text-slate-600",
  low: "bg-amber-50 text-amber-700",
  needs_human_review: "bg-orange-50 text-orange-700",
};

// Lists detected reference candidates with their review-support confidence
// labels. There is no "verified" label: matching is review support, not
// verification.
export default function CadReferenceCandidatePanel({
  candidates,
}: {
  candidates: CadReferenceCandidate[];
}) {
  if (candidates.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No reference candidates detected.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Reference candidates
      </h3>
      <ul className="mt-3 space-y-2">
        {candidates.map((candidate) => (
          <li
            key={candidate.candidateId}
            className="rounded-md border border-slate-200 px-3 py-2"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-sm font-medium text-slate-800">
                {candidate.referenceText}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] ${
                  confidenceStyles[candidate.confidenceLabel] ??
                  confidenceStyles.medium
                }`}
              >
                {candidate.confidenceLabel.replace(/_/g, " ")}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-slate-500">
              {candidate.referenceType.replace(/_/g, " ")} ·{" "}
              {candidate.matchReason}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
