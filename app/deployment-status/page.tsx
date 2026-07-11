"use client";

import { useEffect, useState } from "react";
import type { ApiFailure } from "@/lib/api/client";
import RequestFailureCard from "@/components/RequestFailureCard";
import Link from "next/link";

import BackendStatusBanner from "@/components/BackendStatusBanner";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import SectionCard from "@/components/SectionCard";
import PageHeader from "@/components/PageHeader";
import {
  API_BASE_URL,
  getReadiness,
  getStorageDiagnostics,
  type Readiness,
  type StorageDiagnostics,
} from "@/lib/api";

// Production Foundations Sprint 10 deployment status page. It shows safe
// operational status only: the public backend origin, backend readiness, and
// storage provider status. It never displays secrets, tokens, object storage
// credentials, storage keys, signed URLs, or raw file system paths. Readiness
// and storage values are operational indicators, not engineering outcomes.

// Whether the configured base URL wrongly includes an /api or /api/v1 path.
const URL_INCLUDES_PREFIX = /\/api(\/v1)?\/?$/.test(API_BASE_URL.trim());

function statusClass(status: string): string {
  if (status === "ready" || status === "configured") {
    return "bg-water-50 text-water-800 ring-water-200";
  }
  if (status === "warning" || status === "needs_operator_review") {
    return "bg-amber-50 text-amber-800 ring-amber-200";
  }
  if (status === "unavailable" || status === "missing_required") {
    return "bg-red-50 text-red-700 ring-red-200";
  }
  return "bg-slate-100 text-slate-600 ring-slate-300";
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`badge ${statusClass(status)}`}
      data-testid="status-badge"
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

const troubleshooting = [
  "Redeploy the frontend after changing NEXT_PUBLIC_API_BASE_URL.",
  "NEXT_PUBLIC_API_BASE_URL must be the backend origin only.",
  "Do not include /api/v1 in NEXT_PUBLIC_API_BASE_URL.",
  "Object storage credentials belong on the backend only, never in the frontend.",
  "The public Brookside Meadows demo remains available separately.",
];

export default function DeploymentStatusPage() {
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [storage, setStorage] = useState<StorageDiagnostics | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [failure, setFailure] = useState<ApiFailure | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([getReadiness(), getStorageDiagnostics()]).then(
      ([r, s]) => {
        if (!active) return;
        setReadiness(r.ok ? r.data : null);
        setStorage(s.ok ? s.data : null);
        const firstFailure = [r, s].find((res) => !res.ok);
        setFailure(firstFailure && !firstFailure.ok ? firstFailure : null);
        setLoaded(true);
      },
    );
    return () => {
      active = false;
    };
  }, []);

  return (
    <div>
      <PageHeader
        eyebrow="Operational diagnostics"
        title="Deployment status"
        description="Safe operational status for the live deployment. These are configuration and connectivity indicators only. They do not approve plans, certify compliance, validate design, or make any engineering decision."
      />
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
        {failure ? <RequestFailureCard failure={failure} /> : null}
        <BackendStatusBanner />

        <div className="mt-6 space-y-6">
        {/* Frontend configuration */}
        <SectionCard title="Frontend configuration">
          <dl className="grid gap-3 sm:grid-cols-2">
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Backend origin
              </dt>
              <dd
                className="mt-1 break-all text-sm text-slate-800"
                data-testid="backend-origin"
              >
                {API_BASE_URL}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                API base URL configuration
              </dt>
              <dd className="mt-1 text-sm">
                {URL_INCLUDES_PREFIX ? (
                  <StatusBadge status="needs_operator_review" />
                ) : (
                  <StatusBadge status="configured" />
                )}
              </dd>
            </div>
          </dl>
          {URL_INCLUDES_PREFIX ? (
            <p className="mt-3 text-sm text-amber-800">
              The backend origin includes an /api/v1 path. Set
              NEXT_PUBLIC_API_BASE_URL to the backend origin only and redeploy
              the frontend.
            </p>
          ) : (
            <p className="mt-3 text-sm text-slate-600">
              NEXT_PUBLIC_API_BASE_URL is the backend origin only. The frontend
              appends /api/v1 routes itself.
            </p>
          )}
        </SectionCard>

        {/* Backend readiness */}
        <SectionCard title="Backend readiness">
          {!loaded ? (
            <p className="text-sm text-slate-500">Checking backend readiness...</p>
          ) : readiness ? (
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-700">
                  Overall readiness
                </span>
                <StatusBadge status={readiness.status} />
                {readiness.version ? (
                  <span className="text-xs text-slate-500">
                    version {readiness.version}
                  </span>
                ) : null}
              </div>
              <ul className="mt-4 divide-y divide-slate-100">
                {readiness.checks.map((check) => (
                  <li
                    key={check.category}
                    className="flex items-start justify-between gap-3 py-2"
                  >
                    <div>
                      <p className="text-sm font-medium capitalize text-slate-800">
                        {check.category}
                      </p>
                      <p className="text-xs text-slate-600">{check.message}</p>
                    </div>
                    <StatusBadge status={check.status} />
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-amber-800">
              Backend readiness is unavailable. The backend may be unreachable or
              still starting. The page degrades safely and shows no secrets.
            </p>
          )}
        </SectionCard>

        {/* Storage status */}
        <SectionCard title="Storage status">
          {!loaded ? (
            <p className="text-sm text-slate-500">Checking storage status...</p>
          ) : storage ? (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-700">
                Provider {storage.provider}
              </span>
              <StatusBadge status={storage.status} />
              <span className="text-xs text-slate-600">{storage.message}</span>
            </div>
          ) : (
            <p className="text-sm text-slate-600">
              Storage status requires sign-in. It reports the provider and
              configuration readiness only, never credentials, bucket names,
              storage keys, signed URLs, or paths.{" "}
              <Link href="/login" className="text-water-700 underline">
                Sign in
              </Link>{" "}
              to view it.
            </p>
          )}
        </SectionCard>

        {/* Troubleshooting */}
        <SectionCard
          title="Troubleshooting guidance"
          description="Common deployment configuration checks. No secrets are required."
        >
          <ul className="space-y-2">
            {troubleshooting.map((tip) => (
              <li
                key={tip}
                className="subtle-card flex items-start gap-2 px-3 py-2 text-sm text-slate-700"
              >
                <span aria-hidden="true" className="font-semibold text-water-600">
                  +
                </span>
                {tip}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-slate-500">
            Real project workflows require sign-in. The public demo remains
            available without an account.
          </p>
        </SectionCard>

        <SafetyBoundaryBanner />
      </div>
      </div>
    </div>
  );
}
