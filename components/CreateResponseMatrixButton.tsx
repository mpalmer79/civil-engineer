"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createResponseMatrix } from "@/lib/api";

// Create an applicant response matrix for a project. The matrix organizes
// review-support items and tracks applicant responses for reviewer review. It
// does not resolve or close anything and does not finalize a review outcome.
export default function CreateResponseMatrixButton({
  projectId,
}: {
  projectId: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    setBusy(true);
    setError(null);
    const result = await createResponseMatrix(projectId);
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not create the response matrix.");
      return;
    }
    router.refresh();
  };

  return (
    <div>
      <button
        type="button"
        onClick={handleCreate}
        disabled={busy}
        className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Creating..." : "Create response matrix"}
      </button>
      {error ? (
        <p className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}
