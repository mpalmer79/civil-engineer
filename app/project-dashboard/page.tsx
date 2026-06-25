import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import ProjectDashboard from "@/components/ProjectDashboard";

export default function ProjectDashboardRoute() {
  return (
    <div>
      <PageHeader
        eyebrow="Reviewer command center"
        title="Brookside Meadows project dashboard"
        description="Civil Engineer AI aggregates the entire review-support state into one command center: project health metrics, reviewer attention items with recommended next steps, a project timeline, review readiness checks, reviewer notes, and links into the existing modules. The dashboard organizes review-support work and links into existing modules rather than replacing them. It does not approve plans, certify compliance, verify CAD, validate design, close or resolve issues, or replace a licensed Professional Engineer."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <SectionCard title="What the command center does">
          <p className="text-sm text-slate-600">
            The Project Dashboard answers what needs attention right now, what
            changed since the last round, what is carried forward, what CAD
            findings still need review, what applicant responses need mapping,
            what response items are ready for human review, what resubmittals are
            waiting for comparison, what is ready for handoff, where evidence is
            incomplete, and what the reviewer should do next. It deep links into
            CAD Intake, Review Cycles, Workflow Board, Response Package, Review
            Packet, Sheet Viewer, Plan Sheets, and CAD Review. Every status is a
            review-support status. The dashboard does not approve, certify,
            verify, validate, close, or resolve anything.
          </p>
        </SectionCard>

        <ProjectDashboard />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
