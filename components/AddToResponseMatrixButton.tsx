"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  addChecklistItemToMatrix,
  addFindingToMatrix,
  type ResponseMatrix,
} from "@/lib/api";

// Add a reviewer finding or checklist review item to a response matrix. The
// matrix organizes review-support items and tracks applicant responses for
// reviewer review. Adding an item does not approve, certify, verify, resolve, or
// close anything.
export default function AddToResponseMatrixButton({
  projectId,
  sourceType,
  sourceId,
  matrices,
}: {
  projectId: string;
  sourceType: "finding" | "checklist-item";
  sourceId: string;
  matrices: ResponseMatrix[];
}) {
  const router = useRouter();
  const [matrixId, setMatrixId] = useState(
    matrices.length > 0 ? matrices[0].responseMatrixId : "",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleAdd = async () => {
    if (!matrixId) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    const result =
      sourceType === "finding"
        ? await addFindingToMatrix(projectId, matrixId, sourceId)
        : await addChecklistItemToMatrix(projectId, matrixId, sourceId);
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not add this item to the response matrix.");
      return;
    }
    setMessage("Added to the response matrix for reviewer review.");
    router.refresh();
  };

  if (matrices.length === 0) {
    return (
      <div className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Add to response matrix
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          No response matrix exists for this project yet. Create one from the{" "}
          <a
            href={`/projects/${projectId}/response-matrix`}
            className="text-water-700 hover:underline"
          >
            response matrix page
          </a>{" "}
          first, then add this item for reviewer review.
        </p>
      </div>
    );
  }

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Add to response matrix
      </h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        Adding this item to a response matrix tracks applicant responses for
        reviewer review. It does not finalize a review outcome.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <select
          value={matrixId}
          onChange={(e) => setMatrixId(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          {matrices.map((m) => (
            <option key={m.responseMatrixId} value={m.responseMatrixId}>
              {m.name}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleAdd}
          disabled={busy || !matrixId}
          className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Adding..." : "Add to response matrix"}
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
