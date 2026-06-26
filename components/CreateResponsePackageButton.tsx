"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createResponsePackage } from "@/lib/api";

// Create a reviewer response package for a project. A response package assembles
// reviewer-selected records into a controlled communication artifact. It does not
// approve a project, certify compliance, resolve an issue, or close an issue.
const PACKAGE_TYPES = [
  { value: "initial_review_comment_letter", label: "Initial review comment letter" },
  {
    value: "resubmittal_review_comment_letter",
    label: "Resubmittal review comment letter",
  },
  { value: "checklist_review_summary", label: "Checklist review summary" },
  { value: "response_matrix_summary", label: "Response matrix summary" },
  { value: "reviewer_handoff_package", label: "Reviewer handoff package" },
];

export default function CreateResponsePackageButton({
  projectId,
}: {
  projectId: string;
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [packageType, setPackageType] = useState(PACKAGE_TYPES[0].value);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    setBusy(true);
    setError(null);
    const result = await createResponsePackage(projectId, {
      packageTitle: title.trim() || undefined,
      packageType,
    });
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not create the response package.");
      return;
    }
    router.refresh();
  };

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Create a response package
      </h3>
      <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        A response package assembles reviewer-selected records for reviewer
        handoff. It does not finalize a review outcome.
      </p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Package title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Initial review comments"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Package type
          </label>
          <select
            value={packageType}
            onChange={(e) => setPackageType(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            {PACKAGE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>
      {error ? (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}
      <button
        type="button"
        onClick={handleCreate}
        disabled={busy}
        className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Creating..." : "Create response package"}
      </button>
    </div>
  );
}
