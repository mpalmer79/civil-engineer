"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import {
  getCurrentUser,
  listMyOrganizations,
  listMyProjects,
  type CurrentUser,
  type Organization,
  type UserProject,
} from "@/lib/api";

export default function AccountPage() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [orgs, setOrgs] = useState<Organization[] | null>(null);
  const [projects, setProjects] = useState<UserProject[] | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([
      getCurrentUser(),
      listMyOrganizations(),
      listMyProjects(),
    ]).then(([u, o, p]) => {
      if (!active) return;
      setUser(u);
      setOrgs(o);
      setProjects(p);
      setLoaded(true);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div>
      <PageHeader
        eyebrow="Account"
        title="My account"
        description="Your signed-in identity, organizations, and accessible projects. Roles control who can review records; they do not determine engineering outcomes."
      />
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        {loaded && !user ? (
          <SectionCard title="Not signed in">
            <p className="text-sm text-slate-600">
              You are not signed in.{" "}
              <Link href="/login" className="text-water-700 hover:underline">
                Sign in
              </Link>{" "}
              to view your account.
            </p>
          </SectionCard>
        ) : null}

        {user ? (
          <SectionCard title="Profile">
            <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
              <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
                <dt className="text-sm font-semibold text-slate-500">Name</dt>
                <dd className="text-sm text-slate-800">{user.displayName}</dd>
              </div>
              <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
                <dt className="text-sm font-semibold text-slate-500">Email</dt>
                <dd className="text-sm text-slate-800">{user.email}</dd>
              </div>
            </dl>
          </SectionCard>
        ) : null}

        {user ? (
          <SectionCard title="Organizations">
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
                      {o.role ?? o.organizationType}
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

        {user ? (
          <SectionCard title="Accessible projects">
            {projects && projects.length > 0 ? (
              <ul className="space-y-2">
                {projects.map((p) => (
                  <li
                    key={p.projectId}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 p-3 text-sm"
                  >
                    <Link
                      href={`/projects/${p.projectId}`}
                      className="font-semibold text-water-700 hover:underline"
                    >
                      {p.projectName}
                    </Link>
                    <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                      {p.accessLevel ?? (p.demoPublic ? "public demo" : "member")}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-600">
                No accessible projects yet. Create one from{" "}
                <Link href="/projects/new" className="text-water-700 hover:underline">
                  New project
                </Link>
                .
              </p>
            )}
          </SectionCard>
        ) : null}
      </div>
    </div>
  );
}
