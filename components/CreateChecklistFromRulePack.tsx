"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createProjectChecklistFromRulePack } from "@/lib/api";

// Create a project checklist from a reusable rule pack. A checklist is the
// reviewer's working copy of a rule pack for one project. It is review-support
// only and does not approve, certify, or validate anything.
export default function CreateChecklistFromRulePack({
  projectId,
  rulePacks,
}: {
  projectId: string;
  rulePacks: { rulePackId: string; name: string; itemCount: number }[];
}) {
  const router = useRouter();
  const [rulePackId, setRulePackId] = useState(
    rulePacks[0]?.rulePackId ?? "",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!rulePackId) {
      setError("Select a rule pack.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await createProjectChecklistFromRulePack(projectId, {
      rulePackId,
    });
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not create the checklist.");
      return;
    }
    setMessage(
      `Checklist created with ${result.data.itemCount} item(s). It is review-support only.`,
    );
    router.refresh();
  };

  if (rulePacks.length === 0) {
    return (
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
        No rule packs are available to create a checklist from.
      </p>
    );
  }

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Create checklist from a rule pack
      </h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        A rule pack is a review-support template, not a legal determination. The
        checklist is the reviewer&rsquo;s working copy for this project.
      </p>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <div className="min-w-[16rem]">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Rule pack
          </label>
          <select
            value={rulePackId}
            onChange={(e) => setRulePackId(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            {rulePacks.map((p) => (
              <option key={p.rulePackId} value={p.rulePackId}>
                {p.name} ({p.itemCount} items)
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={handleCreate}
          disabled={busy}
          className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Creating..." : "Create checklist"}
        </button>
      </div>
      {error ? (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mt-3 rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
          {message}
        </p>
      ) : null}
    </div>
  );
}
