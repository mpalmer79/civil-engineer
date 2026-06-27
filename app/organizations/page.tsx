"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import StatusChip from "@/components/StatusChip";
import {
  listMyOrganizations,
  isSignedIn,
  type Organization,
} from "@/lib/api";

export default function OrganizationsPage() {
  const [orgs, setOrgs] = useState<Organization[] | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    let active = true;
    setSignedIn(isSignedIn());
    listMyOrganizations().then((o) => {
      if (!active) return;
      setOrgs(o);
      setLoaded(true);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div>
      <PageHeader
        eyebrow="Access control"
        title="Organizations"
        description="Organizations you belong to. Organization roles control who can review records and manage project access. They do not determine engineering outcomes."
      />
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        {loaded && !signedIn ? (
          <EmptyState
            title="Sign in required"
            description="Organizations control who can review records and manage project access. Sign in to view the organizations you belong to."
            action={
              <Link href="/login" className="btn btn-primary btn-sm">
                Sign in
              </Link>
            }
          />
        ) : null}

        {signedIn ? (
          orgs && orgs.length > 0 ? (
            <div className="list-container">
              {orgs.map((o) => (
                <div
                  key={o.organizationId}
                  className="flex flex-col gap-2 px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between"
                >
                  <Link
                    href={`/organizations/${o.organizationId}`}
                    className="font-semibold text-water-700 hover:underline"
                  >
                    {o.organizationName}
                  </Link>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusChip label={o.organizationType} />
                    <StatusChip
                      tone="brand"
                      prefix="Role:"
                      label={o.role ?? "member"}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : loaded ? (
            <EmptyState
              title="No organizations yet"
              description="You are not a member of any organization yet. An organization admin can add you, or you can create one when registering an account."
            />
          ) : null
        ) : null}
      </div>
    </div>
  );
}
