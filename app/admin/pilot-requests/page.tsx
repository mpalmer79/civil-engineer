"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import EmptyState from "@/components/EmptyState";
import StatusChip from "@/components/StatusChip";
import PilotReleaseNote from "@/components/PilotReleaseNote";
import {
  listPilotRequests,
  type PilotListResult,
  type PilotRequestRecord,
} from "@/lib/api";

// Protected pilot request operator view. It uses the admin-gated
// GET /api/v1/pilot-requests route, so an anonymous or non-admin visitor sees an
// honest access state rather than any data. There is no public list endpoint and
// no file-upload control here. Finer-grained, dedicated pilot-operator roles are
// future work; organization admin is the current operator gate.

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

function RequestCard({ request }: { request: PilotRequestRecord }) {
  return (
    <li className="surface-card p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900">
          {request.firmName || "Unknown firm"}
        </h3>
        <div className="flex flex-wrap items-center gap-2">
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
          <span className="font-semibold text-slate-500">Notes: </span>
          {request.notes}
        </p>
      ) : null}
      {request.createdAt ? (
        <p className="mt-3 text-xs text-slate-400">Received {request.createdAt}</p>
      ) : null}
    </li>
  );
}

export default function PilotRequestsAdminPage() {
  const [result, setResult] = useState<PilotListResult | null>(null);

  useEffect(() => {
    let active = true;
    listPilotRequests().then((r) => {
      if (active) setResult(r);
    });
    return () => {
      active = false;
    };
  }, []);

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
          result.data.length > 0 ? (
            <ul className="space-y-4" data-testid="pilot-request-list">
              {result.data.map((request) => (
                <RequestCard key={request.pilotRequestId} request={request} />
              ))}
            </ul>
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
          )
        ) : null}
      </div>
    </div>
  );
}
