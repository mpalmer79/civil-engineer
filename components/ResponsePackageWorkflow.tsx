"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  createPackageRevision,
  generateCommentLetterDraft,
  issueResponsePackage,
  markPackageReadyForHandoff,
} from "@/lib/api";

// Package-level reviewer actions: generate a deterministic comment letter draft,
// mark the package ready for reviewer handoff, issue the package, and start a
// revision. Issuing a package records a reviewer communication only. It does not
// approve a project, certify compliance, resolve an issue, or close an issue.
export default function ResponsePackageWorkflow({
  projectId,
  packageId,
}: {
  projectId: string;
  packageId: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

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
      <h3 className="text-lg font-semibold text-slate-900">Package workflow</h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        Package issuance records a reviewer communication. It does not finalize a
        review outcome.
      </p>
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() =>
            run(
              "generate",
              async () => {
                const result = await generateCommentLetterDraft(
                  projectId,
                  packageId,
                );
                if (result.ok && result.data) {
                  router.push(
                    `/projects/${projectId}/comment-letter-drafts/${result.data.commentLetterDraftId}`,
                  );
                }
                return result;
              },
              "Comment letter draft created.",
            )
          }
          disabled={busy !== null}
          className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          {busy === "generate" ? "Generating..." : "Generate comment letter draft"}
        </button>
        <button
          type="button"
          onClick={() =>
            run(
              "ready",
              () => markPackageReadyForHandoff(projectId, packageId),
              "Package marked ready for reviewer handoff.",
            )
          }
          disabled={busy !== null}
          className="rounded-lg border border-water-600 px-4 py-2 text-sm font-semibold text-water-700 hover:bg-water-50 disabled:opacity-60"
        >
          {busy === "ready" ? "Updating..." : "Mark ready for reviewer handoff"}
        </button>
        <button
          type="button"
          onClick={() =>
            run(
              "issue",
              () => issueResponsePackage(projectId, packageId),
              "Package issued by reviewer.",
            )
          }
          disabled={busy !== null}
          className="rounded-lg border border-water-600 px-4 py-2 text-sm font-semibold text-water-700 hover:bg-water-50 disabled:opacity-60"
        >
          {busy === "issue" ? "Issuing..." : "Issue package by reviewer"}
        </button>
        <button
          type="button"
          onClick={() =>
            run(
              "revision",
              () => createPackageRevision(projectId, packageId),
              "Package revision started. Prior issued records are preserved.",
            )
          }
          disabled={busy !== null}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
        >
          {busy === "revision" ? "Starting..." : "Create revision"}
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
