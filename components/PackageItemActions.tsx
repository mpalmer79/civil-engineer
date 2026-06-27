"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  updateResponsePackageItem,
  type ReviewerResponsePackageItem,
} from "@/lib/api";

// Per-item reviewer controls: toggle whether an item is included in the comment
// letter and update its review-support status. These are review-support workflow
// labels only. Nothing here approves, resolves, or closes anything.
const ITEM_STATUS_OPTIONS = [
  { value: "item_draft", label: "Item draft" },
  { value: "needs_reviewer_confirmation", label: "Needs reviewer confirmation" },
  { value: "ready_for_reviewer_handoff", label: "Ready for reviewer handoff" },
  { value: "carried_forward_for_review", label: "Carried forward for review" },
  { value: "reviewer_note_added", label: "Reviewer note added" },
];

export default function PackageItemActions({
  projectId,
  item,
}: {
  projectId: string;
  item: ReviewerResponsePackageItem;
}) {
  const router = useRouter();
  const [status, setStatus] = useState(item.itemStatus);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (
    kind: string,
    payload: { includeInLetter?: boolean; itemStatus?: string },
  ) => {
    setBusy(kind);
    setError(null);
    const result = await updateResponsePackageItem(
      projectId,
      item.responsePackageItemId,
      payload,
    );
    setBusy(null);
    if (!result.ok) {
      setError(result.error ?? "Action failed.");
      return;
    }
    router.refresh();
  };

  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={() => run("include", { includeInLetter: !item.includeInLetter })}
        disabled={busy !== null}
        className="btn btn-secondary btn-sm"
      >
        {item.includeInLetter ? "Exclude from letter" : "Include in letter"}
      </button>
      <label className="sr-only" htmlFor={`item-status-${item.responsePackageItemId}`}>
        Item status
      </label>
      <select
        id={`item-status-${item.responsePackageItemId}`}
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        className="form-input w-auto py-2 text-sm"
      >
        {ITEM_STATUS_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={() => run("status", { itemStatus: status })}
        disabled={busy !== null}
        className="btn btn-secondary btn-sm"
      >
        {busy === "status" ? "Saving..." : "Update status"}
      </button>
      {error ? <span className="text-xs text-red-700">{error}</span> : null}
    </div>
  );
}
