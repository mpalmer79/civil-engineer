"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { registerProjectDocument, uploadProjectDocument } from "@/lib/api";

const DOCUMENT_TYPES = [
  "plan_set",
  "stormwater_report",
  "grading_plan",
  "drainage_calculations",
  "narrative",
  "correspondence",
  "other",
];

// Form to register document metadata, or optionally upload a document file, for
// a real project record. Registration and upload record intake metadata only.
// They never imply that a document was approved, certified, or verified.
export default function DocumentRegisterForm({
  projectId,
}: {
  projectId: string;
}) {
  const router = useRouter();
  const [mode, setMode] = useState<"register" | "upload">("register");
  const [originalFileName, setOriginalFileName] = useState("");
  const [documentType, setDocumentType] = useState("plan_set");
  const [purpose, setPurpose] = useState("");
  const [expectedKeyInformation, setExpectedKeyInformation] = useState("");
  const [revisionLabel, setRevisionLabel] = useState("");
  const [revisionDate, setRevisionDate] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setBusy(true);
    setError(null);
    if (mode === "upload") {
      if (!file) {
        setError("Choose a file to upload.");
        setBusy(false);
        return;
      }
      const result = await uploadProjectDocument(projectId, file, {
        documentType,
        purpose,
        revisionLabel,
      });
      setBusy(false);
      if (!result.ok) {
        setError(result.error ?? "Upload failed.");
        return;
      }
      router.push(`/projects/${projectId}/documents`);
      return;
    }

    if (!originalFileName.trim()) {
      setError("Original file name is required.");
      setBusy(false);
      return;
    }
    const result = await registerProjectDocument(projectId, {
      originalFileName: originalFileName.trim(),
      documentType,
      purpose,
      expectedKeyInformation,
      revisionLabel,
      revisionDate,
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Could not register the document.");
      return;
    }
    router.push(`/projects/${projectId}/documents`);
  };

  return (
    <div className="surface-card p-6">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setMode("register")}
          className={`rounded-md px-3 py-1.5 text-sm font-semibold ${
            mode === "register"
              ? "bg-water-600 text-white"
              : "bg-slate-100 text-slate-600"
          }`}
        >
          Register metadata
        </button>
        <button
          type="button"
          onClick={() => setMode("upload")}
          className={`rounded-md px-3 py-1.5 text-sm font-semibold ${
            mode === "upload"
              ? "bg-water-600 text-white"
              : "bg-slate-100 text-slate-600"
          }`}
        >
          Upload file
        </button>
      </div>

      <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        {mode === "upload"
          ? "Uploaded files are stored for review support only. They are not parsed in this sprint and are not approved or verified."
          : "Register the document metadata. Sprint 1 records intake metadata; this does not approve or verify the document."}
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {mode === "register" ? (
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Original file name
            </label>
            <input
              type="text"
              value={originalFileName}
              onChange={(e) => setOriginalFileName(e.target.value)}
              placeholder="Stormwater Report.pdf"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        ) : (
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              File
            </label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        )}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Document type
          </label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            {DOCUMENT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Revision label
          </label>
          <input
            type="text"
            value={revisionLabel}
            onChange={(e) => setRevisionLabel(e.target.value)}
            placeholder="Rev A"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        {mode === "register" ? (
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Revision date
            </label>
            <input
              type="text"
              value={revisionDate}
              onChange={(e) => setRevisionDate(e.target.value)}
              placeholder="2026-06-01"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        ) : null}
      </div>

      <div className="mt-3">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Purpose
        </label>
        <textarea
          value={purpose}
          onChange={(e) => setPurpose(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      {mode === "register" ? (
        <div className="mt-3">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Expected key information
          </label>
          <textarea
            value={expectedKeyInformation}
            onChange={(e) => setExpectedKeyInformation(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
      ) : null}

      {error ? (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={busy}
        className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy
          ? "Saving..."
          : mode === "upload"
            ? "Upload document"
            : "Register document"}
      </button>
    </div>
  );
}
