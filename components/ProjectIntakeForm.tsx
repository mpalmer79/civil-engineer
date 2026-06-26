"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createProject } from "@/lib/api";

// Form to create a real, user-created project record. Creating a project is a
// review-support intake action. It does not approve plans, certify compliance,
// verify CAD, validate design, or make any final engineering decision.
export default function ProjectIntakeForm() {
  const router = useRouter();
  const [projectName, setProjectName] = useState("");
  const [projectType, setProjectType] = useState("Residential subdivision");
  const [jurisdiction, setJurisdiction] = useState("");
  const [reviewType, setReviewType] = useState(
    "Site plan stormwater review",
  );
  const [reviewDomain, setReviewDomain] = useState("stormwater");
  const [locationContext, setLocationContext] = useState("");
  const [acreage, setAcreage] = useState("");
  const [disturbedArea, setDisturbedArea] = useState("");
  const [proposedLots, setProposedLots] = useState("");
  const [applicantName, setApplicantName] = useState("");
  const [applicantOrganization, setApplicantOrganization] = useState("");
  const [designEngineerName, setDesignEngineerName] = useState("");
  const [designFirm, setDesignFirm] = useState("");
  const [submissionReference, setSubmissionReference] = useState("");
  const [summary, setSummary] = useState("");
  const [parcelIds, setParcelIds] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!projectName.trim()) {
      setError("Project name is required.");
      return;
    }
    setBusy(true);
    setError(null);
    const result = await createProject({
      projectName: projectName.trim(),
      projectType: projectType.trim(),
      jurisdiction: jurisdiction.trim(),
      reviewType: reviewType.trim(),
      reviewDomain: reviewDomain.trim(),
      locationContext: locationContext.trim(),
      acreage: acreage ? Number(acreage) : null,
      disturbedArea: disturbedArea ? Number(disturbedArea) : null,
      proposedLots: proposedLots ? Number(proposedLots) : null,
      summary: summary.trim(),
      applicantName: applicantName.trim(),
      applicantOrganization: applicantOrganization.trim(),
      designEngineerName: designEngineerName.trim(),
      designFirm: designFirm.trim(),
      submissionReference: submissionReference.trim(),
      parcelIds: parcelIds
        .split(",")
        .map((p) => p.trim())
        .filter(Boolean),
    });
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not create the project record.");
      return;
    }
    router.push(`/projects/${result.data.projectId}`);
  };

  const field = (
    label: string,
    value: string,
    onChange: (v: string) => void,
    placeholder = "",
    type = "text",
  ) => (
    <div>
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
      />
    </div>
  );

  return (
    <div className="surface-card p-6">
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
        This creates a real review-support project record. It requires human
        review and does not approve plans or make engineering decisions.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {field("Project name", projectName, setProjectName, "Maple Commons Stormwater Review")}
        {field("Project type", projectType, setProjectType)}
        {field("Jurisdiction", jurisdiction, setJurisdiction, "Town of Riverton")}
        {field("Review type", reviewType, setReviewType)}
        {field("Review domain", reviewDomain, setReviewDomain)}
        {field("Location context", locationContext, setLocationContext)}
        {field("Acreage", acreage, setAcreage, "4.2", "number")}
        {field("Disturbed area (acres)", disturbedArea, setDisturbedArea, "3.1", "number")}
        {field("Proposed lots", proposedLots, setProposedLots, "1", "number")}
        {field("Applicant name", applicantName, setApplicantName)}
        {field("Applicant organization", applicantOrganization, setApplicantOrganization)}
        {field("Design engineer name", designEngineerName, setDesignEngineerName)}
        {field("Design firm", designFirm, setDesignFirm)}
        {field("Submission reference", submissionReference, setSubmissionReference)}
        {field("Parcel IDs (comma separated)", parcelIds, setParcelIds, "12-34-567")}
      </div>
      <div className="mt-3">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Summary
        </label>
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={3}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      {error ? (
        <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={busy || !projectName.trim()}
        className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
      >
        {busy ? "Creating..." : "Create project record"}
      </button>
    </div>
  );
}
