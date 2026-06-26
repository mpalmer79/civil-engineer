import Link from "next/link";
import HeroMap from "@/components/HeroMap";
import MetricCard from "@/components/MetricCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import SectionCard from "@/components/SectionCard";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import SitePlanIllustration from "@/components/illustrations/SitePlanIllustration";
import WorkflowStepIcon, {
  type WorkflowStepKey,
} from "@/components/illustrations/WorkflowStepIcon";
import MetricIcon, {
  type MetricIconKey,
} from "@/components/illustrations/MetricIcon";
import ArchitectureDiagram from "@/components/illustrations/ArchitectureDiagram";
import { getHotspots, projectMetrics } from "@/lib/api";

const heroCtas = [
  { href: "/guided-demo", label: "See the Guided Demo" },
  { href: "/project-dashboard", label: "Open Project Dashboard" },
  { href: "/cad-intake", label: "Start CAD Intake" },
  { href: "/review-cycles", label: "View Review Cycles" },
  { href: "/workflow-board", label: "Open Workflow Board" },
  { href: "/response-package", label: "Build Response Package" },
  { href: "/review-packet", label: "View Review Packet" },
];

const metricCards: {
  value: string | number;
  label: string;
  accent: "land" | "water" | "amber";
  icon: MetricIconKey;
}[] = [
  { value: `${projectMetrics.acreage}`, label: "Site acres", accent: "land", icon: "site-acres" },
  { value: projectMetrics.proposedLots, label: "Proposed lots", accent: "land", icon: "proposed-lots" },
  { value: projectMetrics.disturbedAcres, label: "Disturbed acres", accent: "land", icon: "disturbed-acres" },
  { value: projectMetrics.documents, label: "Submitted / referenced documents", accent: "water", icon: "documents" },
  { value: projectMetrics.checklistItems, label: "Stormwater checklist items", accent: "water", icon: "checklist" },
  { value: projectMetrics.plantedIssues, label: "Planted review issues", accent: "amber", icon: "review-issues" },
  { value: projectMetrics.evaluationCases, label: "Evaluation cases", accent: "water", icon: "evaluation" },
];

const workflowSteps: {
  title: string;
  detail: string;
  icon: WorkflowStepKey;
}[] = [
  {
    title: "Upload and parse DXF files",
    detail:
      "Upload a DXF file in the browser, validate it, and parse review-support metadata.",
    icon: "intake",
  },
  {
    title: "Review extracted CAD metadata",
    detail:
      "Inspect layers, text, blocks, and reference candidates with confidence labels.",
    icon: "metadata",
  },
  {
    title: "Organize findings",
    detail:
      "Turn checklist gaps and CAD findings into review-support findings with evidence.",
    icon: "findings",
  },
  {
    title: "Build review packets",
    detail:
      "Assemble documents, sheets, findings, and audit evidence into a packet draft.",
    icon: "packet",
  },
  {
    title: "Track workflow items",
    detail:
      "Move items through triage, follow-up, and ready for handoff on the board.",
    icon: "workflow",
  },
  {
    title: "Generate draft response packages",
    detail:
      "Draft an external response grouped by topic with an attachment checklist.",
    icon: "response",
  },
  {
    title: "Manage resubmittals and revision comparisons",
    detail:
      "Record resubmittals and compare DXF metadata between review rounds.",
    icon: "resubmittal",
  },
  {
    title: "View the reviewer command center",
    detail:
      "See attention items, health metrics, a timeline, and recommended next steps.",
    icon: "command-center",
  },
];

const capabilities = [
  {
    title: "Reviewer Command Center",
    href: "/project-dashboard",
    body: "One dashboard that aggregates attention items, health metrics, a timeline, readiness checks, and next steps across every module.",
  },
  {
    title: "Browser DXF Upload",
    href: "/cad-intake",
    body: "Upload a DXF file with extension, size, content type, and readability validation and safe generated storage names.",
  },
  {
    title: "CAD Intake and Metadata Parsing",
    href: "/cad-intake",
    body: "Parse layers, entities, blocks, text, and reference candidates from a real DXF file with the ezdxf library.",
  },
  {
    title: "Plan Sheet Viewer",
    href: "/sheet-viewer",
    body: "Open a plan sheet with seeded hotspot annotations linked to plan consistency findings and references.",
  },
  {
    title: "Review Packet Builder",
    href: "/review-packet",
    body: "Assemble documents, checklist items, findings, sheets, and audit evidence into a structured packet draft.",
  },
  {
    title: "Workflow Board",
    href: "/workflow-board",
    body: "Track review-support items through triage, follow-up, more information, and ready for handoff.",
  },
  {
    title: "Response Package Builder",
    href: "/response-package",
    body: "Draft an external response grouped by topic with editable wording, an attachment checklist, and sign-off.",
  },
  {
    title: "Resubmittal and Revision Comparison",
    href: "/review-cycles",
    body: "Record resubmittals and compare extracted DXF metadata between rounds to surface added, removed, and changed references.",
  },
  {
    title: "Evidence Traceability",
    href: "/review-packet",
    body: "Every finding links back to its source evidence with document and page references in a traceability matrix.",
  },
  {
    title: "Audit Trail",
    href: "/audit",
    body: "Reviewer actions and accesses are recorded as audit events so the decision history is preserved.",
  },
];

const architecture = [
  "Next.js frontend with a TypeScript API client",
  "FastAPI backend with a versioned review-support API",
  "Python DXF metadata parsing with the ezdxf library",
  "Backend and frontend deploy as two separate Railway services",
  "Backend and frontend tests with a coverage gate",
];

export default async function HomePage() {
  const hotspots = await getHotspots();
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-slate-200 bg-white">
        {/* Decorative blueprint site-plan backdrop. Purely illustrative and
            review-support only; it reinforces human-led plan review rather than
            automated approval. Kept very faint so hero text stays readable. */}
        <SitePlanIllustration className="pointer-events-none absolute inset-y-0 right-0 hidden h-full w-2/3 text-slate-500 opacity-[0.07] lg:block" />
        <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <div>
              <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                Stormwater Review Assistant
              </span>
              <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
                Civil Engineer AI
              </h1>
              <p className="mt-2 text-xl font-semibold text-water-700">
                A review-support platform for stormwater plan review
              </p>
              <p className="mt-5 text-lg text-slate-600">
                Civil Engineer AI helps a human reviewer upload and parse DXF
                files, organize findings and evidence, build review packets,
                track a plan review workflow, draft response packages, manage
                resubmittals across rounds, and see the whole review state in one
                reviewer command center.
              </p>

              <div className="mt-6">
                <SafetyBoundaryBanner variant="compact" />
              </div>

              <div className="mt-4">
                <BackendStatusBanner />
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                {heroCtas.map((cta, idx) => (
                  <Link
                    key={cta.href + cta.label}
                    href={cta.href}
                    className={
                      idx === 0
                        ? "rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700"
                        : "rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
                    }
                  >
                    {cta.label}
                  </Link>
                ))}
              </div>
            </div>

            <HeroMap hotspots={hotspots} />
          </div>
        </div>
      </section>

      {/* What is this */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="surface-card p-6">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            What this is
          </h2>
          <p className="mt-3 max-w-3xl text-slate-600">
            Civil Engineer AI is a review-support and evidence-organization
            platform for municipal and civil engineering plan review. It
            structures the work a reviewer does on a stormwater submission:
            intake, evidence organization, findings, packets, workflow, response
            drafting, multi-round resubmittals, and an operational command
            center. The demo project is Brookside Meadows, a synthetic 47-lot
            subdivision with intentionally planted review issues.
          </p>
          <p className="mt-3 max-w-3xl text-slate-600">
            Real DXF upload and metadata extraction live in CAD Intake. The other
            CAD-aware pages, such as CAD Review and the Sheet Viewer, organize
            extracted or seeded CAD-aware metadata for review-support workflows.
            Civil Engineer AI does not parse DWG, verify CAD, validate geometry,
            certify compliance, or approve plans.
          </p>
        </div>
      </section>

      {/* Real-world foundation */}
      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <div className="surface-card border-water-200 p-6">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Real-world foundation now in progress
          </h2>
          <p className="mt-3 max-w-3xl text-slate-600">
            Civil Engineer AI is beginning the move from a seeded demo toward a
            system that supports real project records. Brookside Meadows remains
            the guided demo. Real Project Intake begins persistent review records:
            reviewers can create project records, register or upload documents,
            create review-support findings, and inspect durable audit events.
          </p>
          <p className="mt-3 max-w-3xl text-slate-600">
            Sprint 2 adds PDF page indexing and reviewer-selected evidence
            citations: uploaded PDFs can be indexed into page-level review
            records, and reviewers can cite an exact page or section as evidence
            for a finding. Text extraction covers digital PDFs only. Full OCR and
            automated AI retrieval remain future roadmap items.
          </p>
          <p className="mt-3 max-w-3xl text-slate-600">
            These are real-world foundation sprints, not a production release.
            Full authentication, OCR, jurisdiction rule packs, and an applicant
            portal are future roadmap items. Real project records, page indexing,
            and citations are review-support only and do not approve plans,
            certify compliance, verify CAD, or make final engineering decisions.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href="/projects"
              className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700"
            >
              Open Projects
            </Link>
            <Link
              href="/projects/new"
              className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
            >
              Create a project record
            </Link>
          </div>
        </div>
      </section>

      {/* Metrics */}
      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Brookside Meadows: review fixture at a glance
        </h2>
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-7">
          {metricCards.map((m) => (
            <MetricCard
              key={m.label}
              value={m.value}
              label={m.label}
              accent={m.accent}
              icon={<MetricIcon icon={m.icon} />}
            />
          ))}
        </div>
      </section>

      {/* Core product workflow */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Core product workflow
          </h2>
          <p className="mt-2 max-w-2xl text-slate-600">
            What a reviewer can do, from intake to handoff. Every step keeps the
            evidence under human review.
          </p>
          <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {workflowSteps.map((step, i) => (
              <li key={step.title} className="surface-card p-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-water-50 text-sm font-bold text-water-700">
                    {i + 1}
                  </div>
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-50 text-water-700 ring-1 ring-inset ring-slate-200">
                    <WorkflowStepIcon step={step.icon} />
                  </span>
                </div>
                <p className="mt-3 text-sm font-semibold text-slate-800">
                  {step.title}
                </p>
                <p className="mt-1 text-xs text-slate-600">{step.detail}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Key capabilities */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Key capabilities
        </h2>
        <p className="mt-2 max-w-2xl text-slate-600">
          Each capability is a working module. Open one to explore the Brookside
          Meadows review.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((cap) => (
            <Link
              key={cap.title}
              href={cap.href}
              className="surface-card p-5 transition-colors hover:border-water-400"
            >
              <h3 className="text-base font-semibold text-slate-900">
                {cap.title}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{cap.body}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Technical credibility */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.2fr] lg:items-center">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                What makes it technically credible
              </h2>
              <p className="mt-3 text-slate-600">
                A controlled review workflow wraps structure, real DXF parsing,
                evidence traceability, human review, and an audit trail around
                the data, not a free-form chatbot. Live AI calls are disabled by
                default, so the demo runs deterministically.
              </p>
            </div>
            <SectionCard title="Technical architecture">
              {/* Decorative system diagram. The labels below the diagram carry
                  the meaning for assistive technology; the SVG itself has no
                  embedded text. */}
              <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
                <ArchitectureDiagram className="mx-auto h-auto w-full max-w-md text-slate-500" />
                <div className="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1.5">
                    <span aria-hidden="true" className="h-2 w-2 rounded-sm bg-slate-400" />
                    Next.js frontend
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <span aria-hidden="true" className="h-2 w-2 rounded-sm bg-water-600" />
                    FastAPI backend
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <span aria-hidden="true" className="h-2 w-2 rounded-sm bg-slate-400" />
                    DXF parser
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <span aria-hidden="true" className="h-2 w-2 rounded-sm bg-land-700" />
                    Testing and coverage
                  </span>
                </div>
              </div>
              <ul className="space-y-2">
                {architecture.map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700"
                  >
                    <span aria-hidden="true" className="text-water-600">
                      +
                    </span>
                    {item}
                  </li>
                ))}
              </ul>
            </SectionCard>
          </div>
        </div>
      </section>

      {/* Professional boundary */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <SafetyBoundaryBanner />
      </section>

      {/* Where to start */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="surface-card p-6">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              Where to start
            </h2>
            <p className="mt-3 max-w-3xl text-slate-600">
              New here? The Guided Demo follows one concern end to end, from
              checklist requirement to draft response, so you can see a complete
              review-support workflow without learning every module first.
              Otherwise, open the Project Dashboard for the unified command
              center, or start with CAD Intake to upload and parse a DXF file.
              From there, work the findings into a review packet, track them on
              the workflow board, draft a response package, and manage
              resubmittals across review cycles.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                href="/guided-demo"
                className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700"
              >
                See the Guided Demo
              </Link>
              <Link
                href="/project-dashboard"
                className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                Open Project Dashboard
              </Link>
              <Link
                href="/cad-intake"
                className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                Start CAD Intake
              </Link>
              <Link
                href="/project"
                className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                About the review fixture
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
