"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import PermissionDeniedCard from "@/components/PermissionDeniedCard";
import {
  grantProjectAccess,
  isSignedIn,
  listProjectAccess,
  type ProjectAccessEntry,
} from "@/lib/api";

const ACCESS_LEVELS = [
  "project_admin",
  "senior_reviewer",
  "reviewer",
  "read_only",
  "applicant_placeholder",
];

export default function ProjectAccessPage({
  params,
}: {
  params: { projectId: string };
}) {
  const [entries, setEntries] = useState<ProjectAccessEntry[] | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const [userId, setUserId] = useState("");
  const [accessLevel, setAccessLevel] = useState("reviewer");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = () => {
    listProjectAccess(params.projectId).then((e) => {
      setEntries(e);
      setLoaded(true);
    });
  };

  useEffect(() => {
    setSignedIn(isSignedIn());
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.projectId]);

  const handleGrant = async () => {
    if (!userId.trim()) {
      setError("Enter the user id to grant access to.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await grantProjectAccess(params.projectId, {
      accessLevel,
      userId: userId.trim(),
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Could not grant access.");
      return;
    }
    setMessage("Access granted.");
    setUserId("");
    load();
  };

  return (
    <div>
      <PageHeader
        eyebrow="Access control"
        title="Project access"
        description="Who can view or take reviewer actions on this project. Access controls review records; it does not approve plans, certify compliance, or determine engineering outcomes."
      />
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Link href={`/projects/${params.projectId}`} className="nav-link">
          Back to project
        </Link>

        {loaded && !signedIn ? (
          <PermissionDeniedCard message="Sign in to view and manage project access. Ask a project admin or organization admin for access." />
        ) : null}

        {entries !== null ? (
          <SectionCard title="Current access">
            {entries.length === 0 ? (
              <p className="text-sm text-slate-600">
                No access entries yet, or you do not have access to view them.
              </p>
            ) : (
              <ul className="space-y-2">
                {entries.map((e) => (
                  <li
                    key={e.projectAccessId}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 p-3 text-sm"
                  >
                    <span className="text-slate-800">
                      {e.userId
                        ? `User ${e.userId}`
                        : `Organization ${e.organizationId}`}
                    </span>
                    <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                      {e.accessLevel}
                      {e.isActive ? "" : " (inactive)"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        ) : null}

        {signedIn ? (
          <SectionCard
            title="Grant access"
            description="Project admins can grant access to a user. If you are not a project admin, the grant will be declined."
          >
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  User id
                </label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="user_..."
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Access level
                </label>
                <select
                  value={accessLevel}
                  onChange={(e) => setAccessLevel(e.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                >
                  {ACCESS_LEVELS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {error ? (
              <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </p>
            ) : null}
            {message ? (
              <p className="mt-3 rounded-md bg-land-50 px-3 py-2 text-sm text-land-700">
                {message}
              </p>
            ) : null}
            <button
              type="button"
              onClick={handleGrant}
              disabled={busy}
              className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
            >
              {busy ? "Granting..." : "Grant access"}
            </button>
          </SectionCard>
        ) : null}
      </div>
    </div>
  );
}
