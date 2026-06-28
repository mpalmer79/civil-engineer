"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getReviewPacketPrintView,
  type ReviewPacketPrintView,
} from "@/lib/api";

// Friendly labels for traceability reviewer review action types shown on the
// handoff view. They stay review-support only and never imply approval.
const TRACE_ACTION_LABELS: Record<string, string> = {
  reviewer_confirmed_link: "Confirmed link for review",
  needs_more_information: "Needs more information",
  not_applicable: "Not applicable",
  link_rejected: "Link rejected",
  follow_up_needed: "Follow-up needed",
  needs_review: "Needs review",
};

// Loads the printable review-support view and renders it with a print button.
export default function ReviewPacketPrintPreview({
  packetId,
}: {
  packetId: string;
}) {
  const [data, setData] = useState<ReviewPacketPrintView | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      setData(await getReviewPacketPrintView(packetId));
      setLoaded(true);
    })();
  }, [packetId]);

  if (loaded && !data) {
    return (
      <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
        The backend is required to load the printable view.
      </p>
    );
  }
  if (!data) {
    return (
      <p className="surface-card p-4 text-sm text-slate-500">
        Loading printable view...
      </p>
    );
  }

  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-base font-semibold text-slate-900">
          Reviewer handoff package (draft)
        </h3>
        <button
          type="button"
          onClick={() => window.print()}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
        >
          Open print view
        </button>
      </div>

      <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
        {data.draftNotice}
      </div>

      <div className="mt-4">
        <h4 className="text-lg font-bold text-slate-900">{data.title}</h4>
        <p className="mt-1 text-sm text-slate-600">{data.summary}</p>
      </div>

      <div className="mt-4 space-y-4">
        {data.sections.map((section) => (
          <section key={section.sectionType}>
            <h5 className="text-sm font-semibold text-slate-900">
              {section.title}
            </h5>
            <p className="text-xs text-slate-500">{section.summary}</p>
            {section.items.length > 0 ? (
              <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-700">
                {section.items.map((item) => (
                  <li key={item.itemId}>
                    <span className="font-medium">{item.title}</span>
                    {item.description ? (
                      <span className="text-slate-600">
                        {" "}
                        - {item.description}
                      </span>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ))}
      </div>

      {(data.traceabilityReviewRows ?? []).length > 0 ? (
        <section className="mt-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h5 className="text-sm font-semibold text-slate-900">
              Traceability review state
            </h5>
            <Link
              href={`/projects/${data.projectId}/traceability`}
              className="text-xs font-semibold text-water-700 hover:underline"
            >
              Open project traceability
            </Link>
          </div>
          {data.traceabilityNote ? (
            <p className="mt-1 text-xs text-slate-500">{data.traceabilityNote}</p>
          ) : null}
          <ul className="mt-2 space-y-1 text-sm text-slate-700">
            {(data.traceabilityReviewRows ?? []).map((r) => (
              <li key={r.traceabilityRowKey}>
                <span className="font-medium">
                  {r.checklistTitle ?? "Requirement"}
                </span>
                {": "}
                {r.requiresReviewerConfirmation ? (
                  <span className="text-amber-700">
                    requires reviewer confirmation
                  </span>
                ) : (
                  <span className="text-slate-600">
                    {TRACE_ACTION_LABELS[r.reviewActionType ?? ""] ??
                      r.reviewActionType}
                    {r.createdBy ? (
                      <span className="text-slate-500"> by {r.createdBy}</span>
                    ) : null}
                  </span>
                )}
                {r.reviewerNote ? (
                  <span className="block text-xs italic text-slate-500">
                    &ldquo;{r.reviewerNote}&rdquo;
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="mt-6 rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-600">
        {data.professionalLimitations}
      </div>
    </div>
  );
}
