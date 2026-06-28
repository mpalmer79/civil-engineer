"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import SectionCard from "@/components/SectionCard";
import StatusChip from "@/components/StatusChip";
import {
  getOrganizationUsage,
  isSignedIn,
  listMyOrganizations,
  type Organization,
  type UsageSummary,
} from "@/lib/api";

const LIMIT_LABELS: Record<string, string> = {
  projects: "Projects",
  documents: "Documents uploaded",
  pdf_pages: "PDF pages indexed",
  cad_files: "CAD files parsed",
  review_packets: "Review packets",
  ai_calls: "AI calls (future)",
};

// Workspace usage. Shows advisory usage counters against the organization's plan
// limits with warning states as usage approaches or exceeds a limit. Limits are
// advisory in this phase and do not block actions, which is stated on the page.
export default function WorkspaceUsageClient() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [orgs, setOrgs] = useState<Organization[] | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);

  const primaryOrg = (orgs ?? []).find((o) => o.role === "org_admin") ?? (orgs ?? [])[0];
  const orgId = primaryOrg?.organizationId ?? null;

  useEffect(() => {
    const authed = isSignedIn();
    setSignedIn(authed);
    if (!authed) return;
    listMyOrganizations().then((o) => setOrgs(o));
  }, []);

  useEffect(() => {
    if (orgId) getOrganizationUsage(orgId).then((u) => setUsage(u));
  }, [orgId]);

  if (signedIn === false) {
    return (
      <SectionCard title="Sign in to view usage">
        <p className="text-sm text-slate-600">
          Sign in to see your organization usage against plan limits.
        </p>
        <Link href="/login" className="btn btn-primary btn-sm mt-4">
          Sign in
        </Link>
      </SectionCard>
    );
  }

  if (orgs !== null && !primaryOrg) {
    return (
      <SectionCard title="No organization yet">
        <p className="text-sm text-slate-600">
          Usage is tracked per organization. Create or join one to see usage.
        </p>
      </SectionCard>
    );
  }

  return (
    <div className="space-y-6">
      <SectionCard title="Usage and limits">
        <p className="mb-4 text-sm text-slate-600">
          {usage?.enforcement === "enforced"
            ? "Some usage limits are enforced: an over-limit action is blocked with a clear message. The public Brookside Meadows demo is never affected."
            : "Usage limits are advisory: usage is tracked and shown here, and actions are not blocked. The public Brookside Meadows demo is never affected."}
        </p>
        {usage ? (
          <ul className="list-container">
            {usage.limits.map((limit) => {
              const label = LIMIT_LABELS[limit.key] ?? limit.key;
              const limitText =
                limit.limit === null ? "no metered limit" : String(limit.limit);
              return (
                <li
                  key={limit.key}
                  className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
                >
                  <span className="text-slate-800">
                    {label}
                    {limit.enforced ? (
                      <span className="chip chip-neutral ml-2">enforced</span>
                    ) : null}
                  </span>
                  <span className="flex items-center gap-3">
                    <span className="text-slate-600">
                      {limit.used} / {limitText}
                    </span>
                    <StatusChip label={limit.status} prefix="usage" />
                  </span>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="text-sm text-slate-600">Loading usage...</p>
        )}
      </SectionCard>
    </div>
  );
}
