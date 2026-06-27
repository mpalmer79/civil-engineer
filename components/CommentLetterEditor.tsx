"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  updateCommentLetterDraft,
  type CommentLetterDraft,
} from "@/lib/api";

// Reviewer editor for a deterministic comment letter draft. The reviewer can edit
// each section and mark the draft ready for reviewer handoff. The draft is a
// reviewer communication artifact. It does not approve plans, certify compliance,
// resolve an issue, or close an issue. The boundary statement is fixed and is not
// an editable section.
const FIELDS: { key: keyof CommentLetterDraft; label: string; rows: number }[] =
  [
    { key: "subjectLine", label: "Subject line", rows: 1 },
    { key: "introductionText", label: "Introduction", rows: 3 },
    { key: "projectSummaryText", label: "Project summary", rows: 2 },
    { key: "reviewScopeText", label: "Review scope", rows: 3 },
    { key: "commentItemsText", label: "Review-support comments", rows: 6 },
    { key: "resubmittalSummaryText", label: "Resubmittal summary", rows: 2 },
    { key: "closingText", label: "Closing", rows: 3 },
  ];

export default function CommentLetterEditor({
  projectId,
  draft,
}: {
  projectId: string;
  draft: CommentLetterDraft;
}) {
  const router = useRouter();
  const [values, setValues] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = { title: draft.title };
    for (const f of FIELDS) {
      initial[f.key] = (draft[f.key] as string | null) ?? "";
    }
    return initial;
  });
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const setField = (key: string, value: string) =>
    setValues((prev) => ({ ...prev, [key]: value }));

  const save = async (status?: string) => {
    setBusy(status ?? "save");
    setError(null);
    setMessage(null);
    const result = await updateCommentLetterDraft(
      projectId,
      draft.commentLetterDraftId,
      {
        title: values.title,
        subjectLine: values.subjectLine,
        introductionText: values.introductionText,
        projectSummaryText: values.projectSummaryText,
        reviewScopeText: values.reviewScopeText,
        commentItemsText: values.commentItemsText,
        resubmittalSummaryText: values.resubmittalSummaryText,
        closingText: values.closingText,
        status,
      },
    );
    setBusy(null);
    if (!result.ok) {
      setError(result.error ?? "Could not save the comment letter draft.");
      return;
    }
    setMessage(
      status === "ready_for_reviewer_handoff"
        ? "Comment letter draft marked ready for reviewer handoff."
        : "Comment letter draft saved.",
    );
    router.refresh();
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Edit comment letter draft
      </h3>
      <p className="alert alert-info mt-2">
        This is a reviewer-editable draft generated from deterministic templates.
        It does not finalize a review outcome.
      </p>
      <div className="mt-4 space-y-4">
        <div className="form-field">
          <label htmlFor="cl-title" className="form-label">
            Title
          </label>
          <input
            id="cl-title"
            type="text"
            value={values.title}
            onChange={(e) => setField("title", e.target.value)}
            className="form-input"
          />
        </div>
        {FIELDS.map((f) => (
          <div key={f.key} className="form-field">
            <label htmlFor={`cl-${String(f.key)}`} className="form-label">
              {f.label}
            </label>
            <textarea
              id={`cl-${String(f.key)}`}
              value={values[f.key]}
              onChange={(e) => setField(f.key, e.target.value)}
              rows={f.rows}
              className="form-input"
            />
          </div>
        ))}
      </div>
      {error ? <p className="alert alert-danger mt-3">{error}</p> : null}
      {message ? <p className="alert alert-success mt-3">{message}</p> : null}
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => save()}
          disabled={busy !== null}
          className="btn btn-primary btn-sm"
        >
          {busy === "save" ? "Saving..." : "Save edits"}
        </button>
        <button
          type="button"
          onClick={() => save("ready_for_reviewer_handoff")}
          disabled={busy !== null}
          className="btn btn-secondary btn-sm"
        >
          {busy === "ready_for_reviewer_handoff"
            ? "Updating..."
            : "Mark ready for reviewer handoff"}
        </button>
      </div>
    </div>
  );
}
