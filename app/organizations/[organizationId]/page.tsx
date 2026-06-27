"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
import PermissionDeniedCard from "@/components/PermissionDeniedCard";
import {
  getOrganization,
  listOrganizationMembers,
  isSignedIn,
  type Membership,
  type Organization,
} from "@/lib/api";

export default function OrganizationDetailPage({
  params,
}: {
  params: { organizationId: string };
}) {
  const [org, setOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<Membership[] | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    let active = true;
    setSignedIn(isSignedIn());
    Promise.all([
      getOrganization(params.organizationId),
      listOrganizationMembers(params.organizationId),
    ]).then(([o, m]) => {
      if (!active) return;
      setOrg(o);
      setMembers(m);
      setLoaded(true);
    });
    return () => {
      active = false;
    };
  }, [params.organizationId]);

  return (
    <div>
      <PageHeader
        eyebrow="Organization"
        title={org?.organizationName ?? "Organization"}
        description="Organization metadata and members. Member roles control review access; they do not approve plans, certify compliance, or determine engineering outcomes."
      />
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Link href="/organizations" className="nav-link">
          Back to organizations
        </Link>

        {loaded && !signedIn ? (
          <SectionCard title="Sign in required">
            <p className="text-sm text-slate-600">
              <Link href="/login" className="text-water-700 hover:underline">
                Sign in
              </Link>{" "}
              to view this organization.
            </p>
          </SectionCard>
        ) : null}

        {loaded && signedIn && !org ? (
          <PermissionDeniedCard message="You do not have access to this organization. Ask an organization admin for access." />
        ) : null}

        {org ? (
          <SectionCard title="Organization metadata">
            <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
              <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
                <dt className="text-sm font-semibold text-slate-500">Type</dt>
                <dd className="text-sm text-slate-800">
                  {org.organizationType}
                </dd>
              </div>
              <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
                <dt className="text-sm font-semibold text-slate-500">
                  Your role
                </dt>
                <dd className="text-sm text-slate-800">{org.role ?? "member"}</dd>
              </div>
            </dl>
          </SectionCard>
        ) : null}

        {org ? (
          <SectionCard title="Members">
            {members && members.length > 0 ? (
              <ul className="list-container">
                {members.map((m) => (
                  <li
                    key={m.membershipId}
                    className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
                  >
                    <span className="text-slate-800">
                      {m.displayName ?? m.userEmail ?? m.userId}
                    </span>
                    <StatusChip label={m.role} prefix="role" />
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No members listed" />
            )}
            <p className="mt-3 text-xs text-slate-500">
              Access control is a local foundation. Enterprise SSO and tenant
              isolation are future roadmap work.
            </p>
          </SectionCard>
        ) : null}
      </div>
    </div>
  );
}
