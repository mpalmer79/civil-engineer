"use client";

import { useState } from "react";

import { submitPilotRequest, type PilotInterestLevel } from "@/lib/api";
import { trackDemoEvent } from "@/lib/analytics";

// Public pilot / design-partner request form. It captures a lead after a visitor
// sees the guided demo, submits it to the backend, and shows an honest success
// state. It collects no file uploads; a checkbox only records that the submitter
// has a sample package to test. Analytics events carry non-sensitive metadata
// only (source route, state) and never form field values.

const PROJECT_TYPES = [
  "Residential subdivision",
  "Commercial site",
  "Stormwater / drainage",
  "Roadway / transportation",
  "Mixed use",
  "Other",
];

const INTEREST_LEVELS: { value: PilotInterestLevel; label: string }[] = [
  { value: "exploring", label: "Exploring options" },
  { value: "evaluating", label: "Evaluating for a project" },
  { value: "ready_to_pilot", label: "Ready to start a pilot" },
];

const SOURCE = "pilot_page";

export default function PilotRequestForm() {
  const [fullName, setFullName] = useState("");
  const [workEmail, setWorkEmail] = useState("");
  const [firmName, setFirmName] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [projectType, setProjectType] = useState("");
  const [primaryPain, setPrimaryPain] = useState("");
  const [interestLevel, setInterestLevel] = useState<PilotInterestLevel | "">("");
  const [notes, setNotes] = useState("");
  const [hasSamplePackage, setHasSamplePackage] = useState(false);

  const [started, setStarted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  // Fire pilot_form_started once, on the first interaction.
  const markStarted = () => {
    if (started) return;
    setStarted(true);
    trackDemoEvent("pilot_form_started", { source: SOURCE });
  };

  const emailLooksValid = (value: string) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (
      !fullName.trim() ||
      !workEmail.trim() ||
      !firmName.trim() ||
      !roleTitle.trim() ||
      !projectType.trim() ||
      !primaryPain.trim() ||
      !interestLevel
    ) {
      setError("Please complete the required fields before submitting.");
      trackDemoEvent("pilot_form_error", { source: SOURCE, reason: "validation" });
      return;
    }
    if (!emailLooksValid(workEmail.trim())) {
      setError("Please enter a valid work email.");
      trackDemoEvent("pilot_form_error", { source: SOURCE, reason: "validation" });
      return;
    }

    setBusy(true);
    setError(null);
    const result = await submitPilotRequest({
      fullName: fullName.trim(),
      workEmail: workEmail.trim(),
      firmName: firmName.trim(),
      roleTitle: roleTitle.trim(),
      projectType: projectType.trim(),
      primaryPain: primaryPain.trim(),
      interestLevel: interestLevel as PilotInterestLevel,
      notes: notes.trim() || undefined,
      hasSamplePackage,
    });
    setBusy(false);

    if (!result.ok) {
      setError(
        result.error ??
          "We could not record your request. Please try again in a moment.",
      );
      trackDemoEvent("pilot_form_error", {
        source: SOURCE,
        reason: result.backendReachable ? "rejected" : "unreachable",
      });
      return;
    }

    trackDemoEvent("pilot_form_submitted", {
      source: SOURCE,
      hasSamplePackage,
    });
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="surface-card p-6" data-testid="pilot-success">
        <span className="chip chip-brand">Pilot request received</span>
        <h2 className="mt-3 text-xl font-semibold text-slate-900">
          Thanks. Your pilot request was received.
        </h2>
        <p className="mt-3 text-slate-600">
          This prototype is currently accepting design-partner conversations. We
          will follow up before requesting any real project files. A human
          reviewer remains responsible for any review-support work.
        </p>
      </div>
    );
  }

  return (
    <form className="surface-card p-6" onSubmit={handleSubmit} noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="form-label" htmlFor="pilot-full-name">
            Full name
          </label>
          <input
            id="pilot-full-name"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            onFocus={markStarted}
            className="form-input w-full"
            required
          />
        </div>
        <div>
          <label className="form-label" htmlFor="pilot-work-email">
            Work email
          </label>
          <input
            id="pilot-work-email"
            type="email"
            value={workEmail}
            onChange={(e) => setWorkEmail(e.target.value)}
            onFocus={markStarted}
            className="form-input w-full"
            required
          />
        </div>
        <div>
          <label className="form-label" htmlFor="pilot-firm-name">
            Firm / company name
          </label>
          <input
            id="pilot-firm-name"
            type="text"
            value={firmName}
            onChange={(e) => setFirmName(e.target.value)}
            onFocus={markStarted}
            className="form-input w-full"
            required
          />
        </div>
        <div>
          <label className="form-label" htmlFor="pilot-role-title">
            Role or title
          </label>
          <input
            id="pilot-role-title"
            type="text"
            value={roleTitle}
            onChange={(e) => setRoleTitle(e.target.value)}
            onFocus={markStarted}
            className="form-input w-full"
            required
          />
        </div>
        <div>
          <label className="form-label" htmlFor="pilot-project-type">
            Project type
          </label>
          <select
            id="pilot-project-type"
            value={projectType}
            onChange={(e) => setProjectType(e.target.value)}
            onFocus={markStarted}
            className="form-input w-full"
            required
          >
            <option value="">Select a project type</option>
            {PROJECT_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="form-label" htmlFor="pilot-interest-level">
            Interest level
          </label>
          <select
            id="pilot-interest-level"
            value={interestLevel}
            onChange={(e) =>
              setInterestLevel(e.target.value as PilotInterestLevel | "")
            }
            onFocus={markStarted}
            className="form-input w-full"
            required
          >
            <option value="">Select an interest level</option>
            {INTEREST_LEVELS.map((level) => (
              <option key={level.value} value={level.value}>
                {level.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4">
        <label className="form-label" htmlFor="pilot-primary-pain">
          Primary pain or current review bottleneck
        </label>
        <textarea
          id="pilot-primary-pain"
          value={primaryPain}
          onChange={(e) => setPrimaryPain(e.target.value)}
          onFocus={markStarted}
          rows={3}
          className="form-input w-full"
          placeholder="For example: avoidable resubmittal cycles from missed review comments."
          required
        />
      </div>

      <div className="mt-4">
        <label className="form-label" htmlFor="pilot-notes">
          Anything else? (optional)
        </label>
        <textarea
          id="pilot-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          onFocus={markStarted}
          rows={2}
          className="form-input w-full"
        />
      </div>

      <label className="mt-4 flex items-start gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={hasSamplePackage}
          onChange={(e) => setHasSamplePackage(e.target.checked)}
          className="mt-1"
        />
        <span>
          I have a sample DXF, plan set, or stormwater package I would like to
          test. (No files are uploaded here; we will follow up first.)
        </span>
      </label>

      {error ? <p className="alert alert-danger mt-4">{error}</p> : null}

      <button
        type="submit"
        disabled={busy}
        className="btn btn-primary mt-5 w-full sm:w-auto"
      >
        {busy ? "Sending request..." : "Request design-partner access"}
      </button>

      <p className="mt-3 text-xs text-slate-500">
        Your request is recorded so we can follow up. No data is sent to any
        third-party service, and no email is sent automatically.
      </p>
    </form>
  );
}
