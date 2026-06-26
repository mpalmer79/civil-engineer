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

// Primary hero calls to action lead with the real project workflow and the
// guided demo. CAD intake is a demo-specific action and is reached from the
// Brookside Meadows demo workflow lower on the page, not from the hero.
const heroCtas = [
  { href: "/projects", label: "Open Projects" },
  { href: "/guided-demo", label: "See the Guided Demo" },
  { href: "/projects/new", label: "Create a project record" },
  { href: "/rule-packs", label: "View Rule Packs" },
];

// Production foundation workflow: the real-world review-support workflow built
// across Sprints 1 through 8. Project-scoped steps link to /projects because the
// workflow starts from an individual project record. Every step is
// review-support only and keeps a human reviewer responsible.
const productionWorkflow: {
  title: string;
  detail: string;
  href: string;
  note: string;
}[] = [
  {
    title: "Create project record",
    detail: "Start a real, persistent review record for a submission.",
    href: "/projects/new",
    note: "Sign in to create",
  },
  {
    title: "Upload documents",
    detail: "Register and store submitted documents through the storage layer.",
    href: "/projects",
    note: "Per project record",
  },
  {
    title: "Index PDF pages",
    detail: "Index digital PDF pages and extract text where it is embedded.",
    href: "/projects",
    note: "Digital PDFs only",
  },
  {
    title: "Cite evidence",
    detail: "Cite an exact page or section as evidence for a finding.",
    href: "/projects",
    note: "Reviewer selected",
  },
  {
    title: "Search evidence",
    detail: "Search indexed page text and queue candidates for review.",
    href: "/projects",
    note: "Requires reviewer confirmation",
  },
  {
    title: "Apply checklist review",
    detail: "Apply a stormwater rule pack and track checklist evidence status.",
    href: "/rule-packs",
    note: "Review-support only",
  },
  {
    title: "Track applicant responses",
    detail: "Record applicant responses in a matrix for reviewer review.",
    href: "/projects",
    note: "Recorded for review",
  },
  {
    title: "Register resubmittals",
    detail: "Register resubmittal rounds and carry items forward for review.",
    href: "/projects",
    note: "Carried forward for review",
  },
  {
    title: "Issue reviewer response package",
    detail:
      "Assemble a package, draft a comment letter, and issue it as a record.",
    href: "/projects",
    note: "Package issued by reviewer",
  },
];

// What is live now: scannable capability groups in place of a paragraph wall.
// Each group summarizes delivered Sprint 1 through 8 capabilities. Brookside
// Meadows is labeled separately as the public guided demo fixture.
const liveNowGroups: { title: string; items: string[] }[] = [
  {
    title: "Project records and access",
    items: [
      "Real project records",
      "Organizations and roles",
      "Project access control",
      "Audit attribution",
    ],
  },
  {
    title: "Documents and evidence",
    items: [
      "Durable storage abstraction",
      "PDF page indexing",
      "Page-level evidence citations",
      "Deterministic evidence retrieval",
    ],
  },
  {
    title: "Review workflow",
    items: [
      "Checklist-driven review",
      "Evidence candidate queue",
      "Draft findings",
      "Applicant response matrix",
      "Resubmittal rounds",
    ],
  },
  {
    title: "Reviewer communication",
    items: [
      "Response package issuance",
      "Deterministic comment letter drafts",
      "Revision history",
      "Ready for reviewer handoff",
    ],
  },
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
                A document-first, evidence-first, reviewer-controlled stormwater
                review-support platform
              </p>
              <p className="mt-5 text-lg text-slate-600">
                Civil Engineer AI is a review-support platform for municipal and
                civil engineering plan review. Reviewers create project records,
                upload and store documents, index PDF pages, cite evidence, apply
                checklist review, track applicant responses, manage resubmittals,
                and issue reviewer response packages. Brookside Meadows remains
                the public guided demo.
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
            Civil Engineer AI structures the work a reviewer does on a stormwater
            submission: real project records, document upload and storage, PDF
            page indexing, evidence citations, deterministic evidence retrieval,
            checklist-driven review, an applicant response matrix, resubmittal
            rounds, and reviewer response packages. The demo project is Brookside
            Meadows, a synthetic 47-lot subdivision with intentionally planted
            review issues.
          </p>
          <p className="mt-3 max-w-3xl text-slate-600">
            Civil Engineer AI supports human plan review. It does not approve
            plans, certify compliance, verify CAD, validate design, declare a
            project safe, make final engineering decisions, resolve or close
            issues, or replace a licensed Professional Engineer.
          </p>
        </div>
      </section>

      {/* Production foundation workflow */}
      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <div className="surface-card border-water-200 p-6">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Production foundation workflow
          </h2>
          <p className="mt-2 max-w-3xl text-slate-600">
            The real-world review-support workflow, built across Sprints 1
            through 8. Project-scoped steps start from an individual project
            record, so they open from Projects. Every step is review-support only
            and keeps a human reviewer responsible.
          </p>
          <ol className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {productionWorkflow.map((step, i) => (
              <li key={step.title}>
                <Link
                  href={step.href}
                  className="surface-card flex h-full flex-col p-5 transition-colors hover:border-water-400"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-water-50 text-sm font-bold text-water-700">
                      {i + 1}
                    </div>
                    <span className="text-sm font-semibold text-slate-800">
                      {step.title}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-slate-600">{step.detail}</p>
                  <span className="badge mt-3 w-fit bg-slate-100 text-slate-600 ring-slate-300">
                    {step.note}
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* What is live now */}
      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          What is live now
        </h2>
        <p className="mt-2 max-w-3xl text-slate-600">
          Delivered review-support capabilities across the production foundation
          sprints. These are review-support indicators and workflows only; none
          approves plans, certifies compliance, or makes a final engineering
          decision.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {liveNowGroups.map((group) => (
            <div key={group.title} className="surface-card p-5">
              <h3 className="text-base font-semibold text-slate-900">
                {group.title}
              </h3>
              <ul className="mt-3 space-y-1.5">
                {group.items.map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-2 text-sm text-slate-700"
                  >
                    <span aria-hidden="true" className="mt-0.5 text-water-600">
                      +
                    </span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="surface-card mt-4 flex flex-col gap-2 border-amber-200 bg-amber-50/40 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-900">
              Brookside Meadows: public guided demo fixture
            </p>
            <p className="mt-1 text-sm text-slate-600">
              A synthetic subdivision used to show the review-support workflow.
              It does not represent a real submission or a real engineering
              outcome.
            </p>
          </div>
          <Link
            href="/guided-demo"
            className="shrink-0 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
          >
            Open the guided demo
          </Link>
        </div>
      </section>

      {/* Public demo vs real project workflow */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Public demo vs real project workflow
          </h2>
          <p className="mt-2 max-w-3xl text-slate-600">
            Some pages are public so a visitor can explore the concept, and some
            require sign in because they hold access-controlled review records.
          </p>
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <div className="surface-card p-6">
              <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                Public demo
              </span>
              <h3 className="mt-3 text-lg font-semibold text-slate-900">
                Brookside Meadows
              </h3>
              <ul className="mt-3 space-y-1.5 text-sm text-slate-700">
                <li>No account required</li>
                <li>Seeded synthetic data</li>
                <li>Shows the concept and review-support workflow</li>
                <li>Read-only guided modules</li>
              </ul>
              <Link
                href="/guided-demo"
                className="mt-4 inline-block rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                See the Guided Demo
              </Link>
            </div>
            <div className="surface-card p-6">
              <span className="badge bg-water-50 text-water-700 ring-water-200">
                Real project workflow
              </span>
              <h3 className="mt-3 text-lg font-semibold text-slate-900">
                Your project records
              </h3>
              <ul className="mt-3 space-y-1.5 text-sm text-slate-700">
                <li>Sign in required</li>
                <li>Project access controlled by organization and role</li>
                <li>
                  Upload documents, index PDFs, create citations, findings,
                  checklists, response matrices, and packages
                </li>
                <li>Actions audit attributed to user identity</li>
              </ul>
              <div className="mt-4 flex flex-wrap gap-3">
                <Link
                  href="/projects"
                  className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700"
                >
                  Open Projects
                </Link>
                <Link
                  href="/login"
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
                >
                  Sign in
                </Link>
              </div>
            </div>
          </div>
          <p className="mt-4 max-w-3xl text-xs text-slate-500">
            No enterprise single sign-on yet, no OCR, no live AI calls, and no
            full applicant portal yet. There is no legal compliance engine, no
            final approval workflow, and no automated engineering validation.
          </p>
        </div>
      </section>

      {/* Metrics */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
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

      {/* Brookside Meadows demo workflow */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Brookside Meadows demo workflow
          </h2>
          <p className="mt-2 max-w-2xl text-slate-600">
            The guided demo modules, from intake to handoff. Every step keeps the
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
          Guided demo modules
        </h2>
        <p className="mt-2 max-w-2xl text-slate-600">
          Each module is a working part of the Brookside Meadows guided demo.
          Open one to explore the review-support workflow.
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
              For the real workflow, open Projects to create a project record,
              upload documents, and work through indexing, citations, checklist
              review, response matrices, and reviewer response packages. New
              here? The Guided Demo follows one concern end to end on Brookside
              Meadows, from checklist requirement to draft response, so you can
              see a complete review-support workflow without learning every
              module first.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                href="/projects"
                className="rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700"
              >
                Open Projects
              </Link>
              <Link
                href="/guided-demo"
                className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                See the Guided Demo
              </Link>
              <Link
                href="/rule-packs"
                className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                View Rule Packs
              </Link>
              <Link
                href="/cad-intake"
                className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                Start CAD Intake (demo)
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
