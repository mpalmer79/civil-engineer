import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import PilotReleaseNote from "@/components/PilotReleaseNote";

// Workspace settings placeholder. Every section below is honestly marked as a
// future capability for the design-partner pilot. Nothing here is active: there
// is no team management, billing, usage metering, or live AI toggle. The page
// exists so an operator can see the intended shape without being misled into
// thinking inactive features work.

export const metadata = {
  title: "Workspace settings",
};

const FUTURE_SECTIONS: { title: string; detail: string }[] = [
  {
    title: "Workspace details",
    detail: "Name and contact details for your workspace. Editing is not enabled yet.",
  },
  {
    title: "Users and team",
    detail: "Invite and manage teammates. Team invitations are a future capability.",
  },
  {
    title: "Billing",
    detail: "Plans and payment. Billing is not active during the design-partner pilot.",
  },
  {
    title: "Usage limits",
    detail: "Review and document quotas. Usage metering is a future capability.",
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
        description="Settings for the design-partner pilot. The sections below are planned capabilities and are not active yet."
        actions={
          <Link href="/workspace" className="btn btn-secondary">
            Back to workspace
          </Link>
        }
      />

      <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <PilotReleaseNote variant="compact" />

        <div className="space-y-4">
          {FUTURE_SECTIONS.map((section) => (
            <SectionCard key={section.title} title={section.title}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="max-w-xl text-sm text-slate-600">{section.detail}</p>
                <span className="chip chip-neutral shrink-0">Coming later</span>
              </div>
            </SectionCard>
          ))}
        </div>
      </div>
    </div>
  );
}
