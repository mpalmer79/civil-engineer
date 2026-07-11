"use client";

import { useEffect, useState } from "react";
import type { ApiFailure } from "@/lib/api/client";
import RequestFailureCard from "@/components/RequestFailureCard";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import EmptyState from "@/components/EmptyState";
import StatusChip from "@/components/StatusChip";
import PilotReleaseNote from "@/components/PilotReleaseNote";
import {
  getCurrentUser,
  isSignedIn,
  listMyOrganizations,
  listMyProjects,
  type CurrentUser,
  type Organization,
  type UserProject,
} from "@/lib/api";

// Release-ready workspace home. A signed-in operator lands here to see their
// identity, organization, accessible projects, the pilot/release state, and
// quick links into the product. It is honest about the pilot posture: no team,
// billing, or account-lifecycle features are claimed as active. The public
// Brookside Meadows demo stays reachable from here without an account.

const BROOKSIDE_ID = "proj_brookside_meadows";

export default function WorkspacePage() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [failure, setFailure] = useState<ApiFailure | null>(null);
  const [orgs, setOrgs] = useState<Organization[] | null>(null);
  const [projects, setProjects] = useState<UserProject[] | null>(null);

  useEffect(() => {
    let active = true;
    const authed = isSignedIn();
    setSignedIn(authed);
    if (!authed) return;
    Promise.all([
      getCurrentUser(),
      listMyOrganizations(),
      listMyProjects(),
    ]).then(([u, o, p]) => {
      if (!active) return;
      setUser(u);
      setOrgs(o.ok ? o.data : null);
      setProjects(p.ok ? p.data : null);
      const firstFailure = [o, p].find((r) => !r.ok);
      setFailure(firstFailure && !firstFailure.ok ? firstFailure : null);
    });
    return () => {
      active = false;
    };
  }, []);

  const isOperator = (orgs ?? []).some((o) => o.role === "org_admin");
  const accessibleProjects = projects ?? [];
  const realProjects = accessibleProjects.filter((p) => !p.demoPublic);
  const primaryOrg = (orgs ?? [])[0];

  const quickLinks: { href: string; label: string; note: string }[] = [
    { href: "/projects", label: "Projects", note: "Open accessible review records" },
    { href: "/workspace/team", label: "Team", note: "Invite and manage teammates" },
    { href: "/workspace/billing", label: "Billing", note: "Plan and billing status (inactive)" },
    { href: "/workspace/usage", label: "Usage", note: "Usage against advisory plan limits" },
    { href: "/guided-demo", label: "Guided demo", note: "Run the Brookside Meadows tour" },
    { href: `/projects/${BROOKSIDE_ID}/command-center`, label: "Command center", note: "Sample project operations" },
    { href: "/pilot", label: "Public pilot form", note: "Share with a design-partner firm" },
  ];
  if (isOperator) {
    quickLinks.push({
      href: "/admin/pilot-requests",
      label: "Pilot requests",
      note: "Review submitted design-partner leads",
    });
  }

  return (
    <div>
      <PageHeader
        eyebrow="Workspace"
        title="Workspace home"
        description="Your signed-in workspace for the design-partner pilot. Open projects, run the guided demo, and review pilot requests. Roles control who can review records; they do not determine engineering outcomes."
      />

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <PilotReleaseNote />

        {signedIn === false ? (
          <SectionCard title="Sign in to your workspace">
            <p className="text-sm text-slate-600">
              You are not signed in. Sign in to see your organization and
              accessible projects. The public Brookside Meadows demo remains
              available without an account.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link href="/login" className="btn btn-primary btn-sm">
                Sign in
              </Link>
              <Link href="/register" className="btn btn-secondary btn-sm">
                Create an account
              </Link>
              <Link href="/guided-demo" className="btn btn-secondary btn-sm">
                Guided demo
              </Link>
            </div>
          </SectionCard>
        ) : null}

        {signedIn ? (
          <>
            <SectionCard title="Workspace">
              <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
                <div className="flex items-center justify-between gap-4 border-b border-slate-100 pb-2">
                  <dt className="text-sm font-semibold text-slate-500">Reviewer</dt>
                  <dd className="text-sm text-slate-800">
                    {user?.displayName ?? "Signed in"}
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-4 border-b border-slate-100 pb-2">
                  <dt className="text-sm font-semibold text-slate-500">Organization</dt>
                  <dd className="text-sm text-slate-800">
                    {primaryOrg?.organizationName ?? "No organization yet"}
                  </dd>
                </div>
              </dl>
              <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
                <MetricCard
                  label="Accessible projects"
                  value={String(accessibleProjects.length)}
                />
                <MetricCard
                  label="Active review projects"
                  value={String(realProjects.length)}
                />
                <MetricCard
                  label="Role"
                  value={isOperator ? "Operator" : "Reviewer"}
                />
              </div>
            </SectionCard>

            <SectionCard title="Quick links">
              <ul className="grid gap-3 sm:grid-cols-2">
                {quickLinks.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="interactive-card flex flex-col gap-1 p-4"
                    >
                      <span className="text-sm font-semibold text-water-700">
                        {link.label}
                      </span>
                      <span className="text-xs text-slate-500">{link.note}</span>
                    </Link>
                  </li>
                ))}
              </ul>
              <div className="mt-4">
                <Link
                  href="/workspace/settings"
                  className="text-sm font-semibold text-water-700 hover:underline"
                >
                  Workspace settings →
                </Link>
              </div>
            </SectionCard>

            <SectionCard title="Accessible projects">
              {accessibleProjects.length > 0 ? (
                <ul className="list-container">
                  {accessibleProjects.map((p) => (
                    <li
                      key={p.projectId}
                      className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
                    >
                      <Link
                        href={`/projects/${p.projectId}`}
                        className="font-semibold text-water-700 hover:underline"
                      >
                        {p.projectName}
                      </Link>
                      <StatusChip
                        label={
                          p.accessLevel ?? (p.demoPublic ? "public demo" : "member")
                        }
                        prefix="access"
                      />
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState
                  title="No accessible projects yet"
                  description="Create a real project review record, or open the public Brookside Meadows demo."
                  action={
                    <Link href="/projects/new" className="btn btn-primary btn-sm">
                      New project
                    </Link>
                  }
                />
              )}
            </SectionCard>
          </>
        ) : null}
      </div>
    </div>
  );
}
