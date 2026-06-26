"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  addChecklistItemsToPackage,
  addFindingsToPackage,
  addMatrixItemsToPackage,
  type ReviewerResponsePackage,
} from "@/lib/api";

// Add a single reviewer-selected record (finding, checklist item, or response
// matrix item) to a response package. Adding a record organizes it into a
// reviewer communication artifact. It does not approve a project, certify
// compliance, resolve an issue, or close an issue.
export default function AddToResponsePackageButton({
  projectId,
  sourceType,
  sourceId,
  packages,
}: {
  projectId: string;
  sourceType: "finding" | "checklist-item" | "matrix-item";
  sourceId: string;
  packages: ReviewerResponsePackage[];
}) {
  const router = useRouter();
  const [packageId, setPackageId] = useState(
    packages.length > 0 ? packages[0].responsePackageId : "",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleAdd = async () => {
    if (!packageId) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    const result =
      sourceType === "finding"
        ? await addFindingsToPackage(projectId, packageId, [sourceId])
        : sourceType === "checklist-item"
          ? await addChecklistItemsToPackage(projectId, packageId, [sourceId])
          : await addMatrixItemsToPackage(projectId, packageId, [sourceId]);
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not add this record to the package.");
      return;
    }
    setMessage("Added to the response package for reviewer handoff.");
    router.refresh();
  };

  if (packages.length === 0) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Add to response package
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          No response package exists for this project yet. Create one from the{" "}
          <a
            href={`/projects/${projectId}/response-packages`}
            className="text-water-700 hover:underline"
          >
            response packages page
          </a>{" "}
          first, then add this record for reviewer handoff.
        </p>
      </div>
    );
  }

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Add to response package
      </h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        Adding this record to a response package organizes it for reviewer
        handoff. It does not finalize a review outcome.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <select
          value={packageId}
          onChange={(e) => setPackageId(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          {packages.map((p) => (
            <option key={p.responsePackageId} value={p.responsePackageId}>
              {p.packageTitle}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleAdd}
          disabled={busy || !packageId}
          className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Adding..." : "Add to response package"}
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
