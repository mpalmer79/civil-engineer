import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import PilotReleaseNote from "@/components/PilotReleaseNote";

// Workspace settings hub. The account lifecycle, team, billing, and usage
// sections are now active and link to their pages. Billing is honestly inactive:
// the plan and usage foundation is in place, but no payment is collected. AI
// provider settings remain a future, opt-in capability.

export const metadata = {
  title: "Workspace settings",
};

const ACTIVE_SECTIONS: {
  title: string;
  detail: string;
  href: string;
  cta: string;
}[] = [
  {
    title: "Team",
    detail:
      "Invite teammates by email, set their role, and revoke pending invitations. Organization admins manage the team.",
    href: "/workspace/team",
    cta: "Manage team",
  },
  {
    title: "Billing",
    detail:
      "View your plan and billing status. Billing is not active in this phase; no payment is collected.",
    href: "/workspace/billing",
    cta: "View billing",
  },
  {
    title: "Usage limits",
    detail:
      "See usage against your plan limits. Limits are advisory and do not block actions.",
    href: "/workspace/usage",
    cta: "View usage",
  },
  {
    title: "Account and password",
    detail:
      "Review your account profile and reset your password from the account page.",
    href: "/me",
    cta: "Open account",
  },
];

const FUTURE_SECTIONS: { title: string; detail: string }[] = [
  {
    title: "Workspace details",
    detail:
      "Name and contact details for your workspace. Editing is not enabled yet.",
  },
  {
    title: "AI provider settings",
    detail:
      "Configure a live AI provider. Live AI is disabled by default and is a future, opt-in capability.",
  },
];

export default function WorkspaceSettingsPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Workspace"
        title="Workspace settings"
        description="Manage your team, plan, usage, and account. Billing is not active in this phase, and live AI remains a future, opt-in capability."
        actions={
          <Link href="/workspace" className="btn btn-secondary">
            Back to workspace
          </Link>
        }
      />

      <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <PilotReleaseNote variant="compact" />

        <div className="space-y-4">
          {ACTIVE_SECTIONS.map((section) => (
            <SectionCard key={section.title} title={section.title}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="max-w-xl text-sm text-slate-600">
                  {section.detail}
                </p>
                <Link href={section.href} className="btn btn-secondary btn-sm shrink-0">
                  {section.cta}
                </Link>
              </div>
            </SectionCard>
          ))}
        </div>

        <div className="space-y-4">
          {FUTURE_SECTIONS.map((section) => (
            <SectionCard key={section.title} title={section.title}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="max-w-xl text-sm text-slate-600">
                  {section.detail}
                </p>
                <span className="chip chip-neutral shrink-0">Coming later</span>
              </div>
            </SectionCard>
          ))}
        </div>
      </div>
    </div>
  );
}
