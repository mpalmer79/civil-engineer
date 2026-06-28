"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import EmptyState from "@/components/EmptyState";
import StatusChip from "@/components/StatusChip";
import PilotReleaseNote from "@/components/PilotReleaseNote";
import { trackDemoEvent } from "@/lib/analytics";
import {
  exportPilotRequestsCsv,
  listPilotRequests,
  updatePilotRequestNotes,
  updatePilotRequestStatus,
  PILOT_STATUSES,
  type PilotListResult,
  type PilotRequestRecord,
  type PilotStatus,
} from "@/lib/api";

// Protected pilot request operations view. It uses the admin-gated pilot APIs, so
// an anonymous or non-admin visitor sees an honest access state rather than any
// data. There is no public list endpoint and no file-upload control. Internal
// notes and status are operator-only. Finer-grained pilot-operator roles are
// future work; organization admin is the current operator gate.

function statusLabel(value: string): string {
  switch (value) {
    case "new":
      return "New";
    case "contacted":
      return "Contacted";
    case "qualified":
      return "Qualified";
    case "active_pilot":
      return "Active pilot";
    case "closed":
      return "Closed";
    case "rejected":
      return "Rejected";
    default:
      return value;
  }
}

function interestLabel(value: string): string {
  switch (value) {
    case "ready_to_pilot":
      return "Ready to pilot";
    case "evaluating":
      return "Evaluating";
    case "exploring":
      return "Exploring";
    default:
      return value || "Not specified";
  }
}

function RequestCard({
  request,
  onStatus,
  onNotes,
}: {
  request: PilotRequestRecord;
  onStatus: (id: string, status: PilotStatus) => Promise<string>;
  onNotes: (id: string, notes: string) => Promise<string>;
}) {
  const [notesDraft, setNotesDraft] = useState(request.internalNotes ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  return (
    <li className="surface-card p-4 sm:p-5" data-testid="pilot-request-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900">
          {request.firmName || "Unknown firm"}
        </h3>
        <div className="flex flex-wrap items-center gap-2">
          <StatusChip prefix="status" label={statusLabel(request.status)} />
          <StatusChip prefix="interest" label={interestLabel(request.interestLevel)} />
          {request.hasSamplePackage ? (
            <span className="chip chip-brand">Has sample package</span>
          ) : null}
        </div>
      </div>
      <dl className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
        <div className="flex justify-between gap-3 border-b border-slate-100 py-1">
          <dt className="text-slate-500">Name</dt>
          <dd className="text-slate-800">{request.fullName}</dd>
        </div>
        <div className="flex justify-between gap-3 border-b border-slate-100 py-1">
          <dt className="text-slate-500">Work email</dt>
          <dd className="break-all text-slate-800">{request.workEmail}</dd>
        </div>
        <div className="flex justify-between gap-3 border-b border-slate-100 py-1">
          <dt className="text-slate-500">Role</dt>
          <dd className="text-slate-800">{request.roleTitle}</dd>
        </div>
        <div className="flex justify-between gap-3 border-b border-slate-100 py-1">
          <dt className="text-slate-500">Project type</dt>
          <dd className="text-slate-800">{request.projectType}</dd>
        </div>
      </dl>
      <p className="mt-3 text-sm text-slate-700">
        <span className="font-semibold text-slate-500">Primary pain: </span>
        {request.primaryPain}
      </p>
      {request.notes ? (
        <p className="mt-2 text-sm text-slate-700">
          <span className="font-semibold text-slate-500">Submitter notes: </span>
          {request.notes}
        </p>
      ) : null}

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="text-sm">
          <span className="form-label">Status</span>
          <select
            aria-label={`Status for ${request.firmName}`}
            className="form-input w-full"
            value={request.status}
            disabled={busy}
            onChange={async (e) => {
              setBusy(true);
              setMessage(await onStatus(request.pilotRequestId, e.target.value as PilotStatus));
              setBusy(false);
            }}
          >
            {PILOT_STATUSES.map((s) => (
              <option key={s} value={s}>
                {statusLabel(s)}
              </option>
            ))}
          </select>
        </label>
        <div className="text-xs text-slate-400 sm:self-end sm:pb-2">
          {request.lastContactedAt
            ? `Last contacted ${request.lastContactedAt}`
            : "Not contacted yet"}
          {request.createdAt ? ` · received ${request.createdAt}` : ""}
        </div>
      </div>

      <label className="mt-3 block text-sm">
        <span className="form-label">Internal notes (operator only)</span>
        <textarea
          aria-label={`Internal notes for ${request.firmName}`}
          className="form-input w-full"
          rows={2}
          value={notesDraft}
          disabled={busy}
          onChange={(e) => setNotesDraft(e.target.value)}
        />
      </label>
      <div className="mt-2 flex items-center gap-3">
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setMessage(await onNotes(request.pilotRequestId, notesDraft));
            setBusy(false);
          }}
        >
          Save notes
        </button>
        {message ? (
          <span className="text-xs text-slate-500" role="status">
            {message}
          </span>
        ) : null}
      </div>
    </li>
  );
}

export default function PilotRequestsAdminPage() {
  const [result, setResult] = useState<PilotListResult | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [interestFilter, setInterestFilter] = useState("");
  const [sampleOnly, setSampleOnly] = useState(false);
  const [search, setSearch] = useState("");
  const [exportMessage, setExportMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    trackDemoEvent("pilot_admin_viewed", {});
    listPilotRequests().then((r) => {
      if (active) setResult(r);
    });
    return () => {
      active = false;
    };
  }, []);

  const records = useMemo(
    () => (result?.status === "ok" ? result.data : []),
    [result],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return records.filter((r) => {
      if (statusFilter && r.status !== statusFilter) return false;
      if (interestFilter && r.interestLevel !== interestFilter) return false;
      if (sampleOnly && !r.hasSamplePackage) return false;
      if (q) {
        const haystack = `${r.firmName} ${r.fullName} ${r.workEmail}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [records, statusFilter, interestFilter, sampleOnly, search]);

  function patchLocal(updated: PilotRequestRecord) {
    setResult((prev) =>
      prev && prev.status === "ok"
        ? {
            status: "ok",
            data: prev.data.map((r) =>
              r.pilotRequestId === updated.pilotRequestId ? updated : r,
            ),
          }
        : prev,
    );
  }

  async function handleStatus(id: string, status: PilotStatus): Promise<string> {
    const r = await updatePilotRequestStatus(id, status, true);
    if (r.status === "ok") {
      patchLocal(r.data);
      trackDemoEvent("pilot_request_status_changed", { status });
      return "Status saved.";
    }
    return "Could not save status. Please try again.";
  }

  async function handleNotes(id: string, notes: string): Promise<string> {
    const r = await updatePilotRequestNotes(id, notes);
    if (r.status === "ok") {
      patchLocal(r.data);
      trackDemoEvent("pilot_request_note_saved", {});
      return "Notes saved.";
    }
    return "Could not save notes. Please try again.";
  }

  async function handleExport() {
    const r = await exportPilotRequestsCsv();
    if (r.status !== "ok") {
      setExportMessage("Export is available to operators only.");
      return;
    }
    trackDemoEvent("pilot_request_exported", {});
    try {
      const blob = new Blob([r.csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "pilot-requests.csv";
      anchor.click();
      URL.revokeObjectURL(url);
      setExportMessage("Exported pilot-requests.csv.");
    } catch {
      setExportMessage("Export prepared.");
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Operator"
        title="Pilot requests"
        description="Submitted design-partner pilot requests. This view is for pilot operators only and is not publicly accessible. No files are uploaded here; follow up with firms before requesting any real project files."
      />

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <PilotReleaseNote variant="compact" />

        {result === null ? (
          <SectionCard title="Loading">
            <p className="text-sm text-slate-600">Loading pilot requests…</p>
          </SectionCard>
        ) : null}

        {result?.status === "unauthorized" ? (
          <SectionCard title="Sign in required">
            <p className="text-sm text-slate-600">
              This operator view requires a signed-in organization admin.{" "}
              <Link href="/login" className="text-water-700 hover:underline">
                Sign in
              </Link>{" "}
              to continue.
            </p>
          </SectionCard>
        ) : null}

        {result?.status === "forbidden" ? (
          <SectionCard title="Operator access required">
            <p className="text-sm text-slate-600">
              Your account is signed in but is not an organization admin. Pilot
              requests are visible to operators only. Finer-grained pilot-operator
              roles are planned; organization admin is the current gate.
            </p>
          </SectionCard>
        ) : null}

        {result?.status === "unreachable" ? (
          <div className="alert alert-warning" role="alert">
            <p className="font-semibold">Backend unavailable</p>
            <p className="mt-1">
              The pilot request list is served by the backend. Start or reach the
              API to view submitted requests.
            </p>
          </div>
        ) : null}

        {result?.status === "error" ? (
          <div className="alert alert-warning" role="alert">
            <p className="font-semibold">Could not load pilot requests</p>
            <p className="mt-1">Please try again in a moment.</p>
          </div>
        ) : null}

        {result?.status === "ok" ? (
          <>
            <SectionCard title="Operations">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <label className="text-sm">
                  <span className="form-label">Status</span>
                  <select
                    aria-label="Filter by status"
                    className="form-input w-full"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <option value="">All statuses</option>
                    {PILOT_STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {statusLabel(s)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-sm">
                  <span className="form-label">Interest</span>
                  <select
                    aria-label="Filter by interest level"
                    className="form-input w-full"
                    value={interestFilter}
                    onChange={(e) => setInterestFilter(e.target.value)}
                  >
                    <option value="">All interest</option>
                    <option value="exploring">Exploring</option>
                    <option value="evaluating">Evaluating</option>
                    <option value="ready_to_pilot">Ready to pilot</option>
                  </select>
                </label>
                <label className="text-sm">
                  <span className="form-label">Search</span>
                  <input
                    aria-label="Search by firm, name, or email"
                    type="text"
                    className="form-input w-full"
                    placeholder="Firm, name, or email"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </label>
                <label className="flex items-center gap-2 text-sm sm:self-end sm:pb-2">
                  <input
                    type="checkbox"
                    checked={sampleOnly}
                    onChange={(e) => setSampleOnly(e.target.checked)}
                  />
                  <span>Has sample package</span>
                </label>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleExport}
                >
                  Export CSV
                </button>
                <Link href="/pilot" className="text-sm font-semibold text-water-700 hover:underline">
                  Public pilot form
                </Link>
                <Link href="/guided-demo" className="text-sm font-semibold text-water-700 hover:underline">
                  Guided demo
                </Link>
                <a
                  href="https://github.com/mpalmer79/civil-engineer/blob/main/docs/PILOT_RELEASE_CHECKLIST.md"
                  className="text-sm font-semibold text-water-700 hover:underline"
                  onClick={() => trackDemoEvent("release_checklist_viewed", {})}
                >
                  Release checklist
                </a>
                {exportMessage ? (
                  <span className="text-xs text-slate-500" role="status">
                    {exportMessage}
                  </span>
                ) : null}
              </div>
            </SectionCard>

            {filtered.length > 0 ? (
              <ul className="space-y-4" data-testid="pilot-request-list">
                {filtered.map((request) => (
                  <RequestCard
                    key={request.pilotRequestId}
                    request={request}
                    onStatus={handleStatus}
                    onNotes={handleNotes}
                  />
                ))}
              </ul>
            ) : records.length > 0 ? (
              <EmptyState
                title="No requests match these filters"
                description="Adjust or clear the filters to see more pilot requests."
              />
            ) : (
              <EmptyState
                title="No pilot requests yet"
                description="When a firm submits the public pilot form, the request appears here for follow-up."
                action={
                  <Link href="/pilot" className="btn btn-secondary btn-sm">
                    View the public pilot form
                  </Link>
                }
              />
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
