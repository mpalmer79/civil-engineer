"use client";

import type { ApplicantResponse, ApplicantResponseMapping } from "@/lib/api";

const confidenceStyles: Record<string, string> = {
  high: "bg-water-50 text-water-700",
  medium: "bg-slate-100 text-slate-600",
  low: "bg-amber-50 text-amber-700",
  needs_human_review: "bg-amber-50 text-amber-700",
};

// Shows suggested and reviewer-created mappings between applicant responses and
// prior response package or workflow items. Mappings are review-support
// suggestions that require human review, never verified matches.
export default function ApplicantResponseMappingPanel({
  mappings,
  responsesById,
  onSuggest,
  busy,
}: {
  mappings: ApplicantResponseMapping[];
  responsesById: Record<string, ApplicantResponse>;
  onSuggest: () => void;
  busy: boolean;
}) {
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">
          Applicant response mappings
        </h3>
        <button
          type="button"
          onClick={onSuggest}
          disabled={busy}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
        >
          {busy ? "Working..." : "Suggest mappings"}
        </button>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        Suggestions use shared keywords between applicant responses and prior
        items. Each mapping is a review-support suggestion and needs human review.
      </p>
      {mappings.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No mappings yet. Use Suggest mappings to generate review-support
          suggestions.
        </p>
      ) : (
        <ul className="mt-4 space-y-2">
          {mappings.map((mapping) => {
            const response = responsesById[mapping.applicantResponseId];
            return (
              <li
                key={mapping.mappingId}
                className="rounded-lg border border-slate-200 px-3 py-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-slate-800">
                    {response
                      ? response.responseTopic
                      : "Applicant response"}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] ${
                      confidenceStyles[mapping.mappingConfidence] ??
                      confidenceStyles.medium
                    }`}
                  >
                    {mapping.mappingConfidence.replace(/_/g, " ")}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-600">
                  {mapping.mappingReason}
                </p>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
