"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  addFindingsToPackage,
  addManualPackageItem,
  type ReviewerFinding,
} from "@/lib/api";

// Add reviewer-selected source records to a response package: project findings or
// a manual reviewer note. Adding records organizes them into a reviewer
// communication artifact. It does not approve a project, certify compliance,
// resolve an issue, or close an issue.
export default function AddSourcesToPackagePanel({
  projectId,
  packageId,
  findings,
}: {
  projectId: string;
  packageId: string;
  findings: ReviewerFinding[];
}) {
  const router = useRouter();
  const [selected, setSelected] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const run = async (
    kind: string,
    fn: () => Promise<{ ok: boolean; error?: string }>,
    okMessage: string,
    onDone?: () => void,
  ) => {
    setBusy(kind);
    setError(null);
    setMessage(null);
    const result = await fn();
    setBusy(null);
    if (!result.ok) {
      setError(result.error ?? "Action failed.");
      return;
    }
    setMessage(okMessage);
    if (onDone) onDone();
    router.refresh();
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Add reviewer-selected records
      </h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        Select reviewer findings to include, or add a manual reviewer note. Each
        record is organized for reviewer handoff.
      </p>

      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Reviewer findings
        </p>
        {findings.length === 0 ? (
          <p className="mt-2 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
            No reviewer findings yet. Create findings before adding them.
          </p>
        ) : (
          <ul className="mt-2 space-y-1">
            {findings.map((f) => (
              <li key={f.findingId} className="text-sm text-slate-700">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selected.includes(f.findingId)}
                    onChange={() => toggle(f.findingId)}
                  />
                  <span>{f.title}</span>
                </label>
              </li>
            ))}
          </ul>
        )}
        <button
          type="button"
          onClick={() =>
            run(
              "findings",
              () => addFindingsToPackage(projectId, packageId, selected),
              "Selected findings added to the response package.",
              () => setSelected([]),
            )
          }
          disabled={busy !== null || selected.length === 0}
          className="mt-3 rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          {busy === "findings" ? "Adding..." : "Add selected findings"}
        </button>
      </div>

      <div className="mt-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Manual reviewer note
        </p>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={2}
          placeholder="Reviewer note text"
          className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={() =>
            run(
              "manual",
              () =>
                addManualPackageItem(projectId, packageId, {
                  reviewerCommentText: note.trim(),
                }),
              "Manual reviewer note added to the response package.",
              () => setNote(""),
            )
          }
          disabled={busy !== null || !note.trim()}
          className="mt-3 rounded-lg border border-water-600 px-4 py-2 text-sm font-semibold text-water-700 hover:bg-water-50 disabled:opacity-60"
        >
          {busy === "manual" ? "Adding..." : "Add manual reviewer note"}
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
