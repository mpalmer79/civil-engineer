"use client";

import { useEffect, useState } from "react";
import {
  updateResponseItemDraftText,
  type ResponsePackageItem,
} from "@/lib/api";

// Editor for a response item draft text. Saving records a revision and moves
// the item to needs_revision. The draft text must avoid final-decision wording;
// the backend rejects prohibited language.
export default function ResponseDraftEditor({
  packageId,
  item,
  reviewerName,
  onItemUpdated,
}: {
  packageId: string;
  item: ResponsePackageItem | null;
  reviewerName: string;
  onItemUpdated: (item: ResponsePackageItem) => void;
}) {
  const [text, setText] = useState(item?.draftText ?? "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setText(item?.draftText ?? "");
    setMessage(null);
  }, [item?.itemId, item?.draftText]);

  if (!item) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Select a response item to edit its draft wording.
      </div>
    );
  }

  const handleSave = async () => {
    setBusy(true);
    setMessage(null);
    const result = await updateResponseItemDraftText(
      packageId,
      item.itemId,
      text,
      undefined,
      reviewerName,
    );
    if (result.ok && result.item) {
      onItemUpdated(result.item);
      setMessage("Draft text saved. Item marked needs revision.");
    } else {
      setMessage(result.error ?? "Could not save the draft text.");
    }
    setBusy(false);
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Draft response text</h3>
      <p className="mt-1 text-xs text-slate-500">
        Plain external-review wording. Avoid approval, certification, or
        validation language.
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={5}
        className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-water-500 focus:outline-none focus:ring-1 focus:ring-water-500"
      />
      <button
        type="button"
        onClick={handleSave}
        disabled={busy || !text.trim()}
        className="mt-3 rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Saving..." : "Save draft text"}
      </button>
      {message ? (
        <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {message}
        </p>
      ) : null}
    </div>
  );
}
