"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
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
          <SectionCard title="Sign in required">
            <p className="text-sm text-slate-600">
              <Link href="/login" className="text-water-700 hover:underline">
                Sign in
              </Link>{" "}
              to view your organizations.
            </p>
          </SectionCard>
        ) : null}

        {signedIn ? (
          <SectionCard>
            {orgs && orgs.length > 0 ? (
              <ul className="space-y-2">
                {orgs.map((o) => (
                  <li
                    key={o.organizationId}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 p-3 text-sm"
                  >
                    <Link
                      href={`/organizations/${o.organizationId}`}
                      className="font-semibold text-water-700 hover:underline"
                    >
                      {o.organizationName}
                    </Link>
                    <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                      {o.organizationType} · {o.role ?? "member"}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-600">
                You are not a member of any organization yet.
              </p>
            )}
          </SectionCard>
        ) : null}
      </div>
    </div>
  );
}
