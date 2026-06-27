import Link from "next/link";

import MarketingMedia from "@/components/MarketingMedia";
import MetricCard from "@/components/MetricCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import MetricIcon, {
  type MetricIconKey,
} from "@/components/illustrations/MetricIcon";
import { marketingMedia } from "@/lib/marketingMedia";
import { projectMetrics } from "@/lib/api";

// Media-first homepage. The visitor reads a short value proposition, sees the
// product visually, then scans compact media-led sections. Long documentation
// paragraphs were compressed into short cards. Every section is review-support
// only and keeps a human reviewer responsible.

// Primary hero call to action leads with the guided demo. Secondary links stay
// short and point at the real workflow surfaces.
const heroCtas = [
  { href: "/start-here", label: "Start the demo" },
  { href: "/projects", label: "Open Projects" },
  { href: "/guided-demo", label: "See the Guided Demo" },
];

// Brookside Meadows fixture metrics, kept as a compact scannable strip.
const metricCards: {
  value: string | number;
  label: string;
  accent: "land" | "water" | "amber";
  icon: MetricIconKey;
}[] = [
  { value: `${projectMetrics.acreage}`, label: "Site acres", accent: "land", icon: "site-acres" },
  { value: projectMetrics.proposedLots, label: "Proposed lots", accent: "land", icon: "proposed-lots" },
  { value: projectMetrics.disturbedAcres, label: "Disturbed acres", accent: "land", icon: "disturbed-acres" },
  { value: projectMetrics.documents, label: "Documents", accent: "water", icon: "documents" },
  { value: projectMetrics.checklistItems, label: "Checklist items", accent: "water", icon: "checklist" },
  { value: projectMetrics.plantedIssues, label: "Planted review issues", accent: "amber", icon: "review-issues" },
];

// Reviewer workflow, compressed to short cards instead of a long list. Each card
// links to a real workflow surface.
const workflowCards: { title: string; detail: string; href: string }[] = [
  {
    title: "Project and documents",
    detail: "Create a project record and store submitted documents.",
    href: "/projects",
  },
  {
    title: "Page-level evidence",
    detail: "Index PDF pages and cite an exact page as evidence.",
    href: "/projects",
  },
  {
    title: "Checklist and findings",
    detail: "Apply a stormwater rule pack and track checklist evidence status.",
    href: "/rule-packs",
  },
  {
    title: "Applicant responses",
    detail: "Record applicant responses in a matrix for reviewer review.",
    href: "/projects",
  },
  {
    title: "Response package",
    detail: "Assemble a package and draft a comment letter as a record.",
    href: "/projects",
  },
  {
    title: "Dashboard and diagnostics",
    detail: "See workload metrics, a reviewer queue, and deployment status.",
    href: "/dashboard",
  },
];

// Technical foundation, as concise capability cards in place of an architecture
// paragraph.
const foundationCards: { title: string; detail: string }[] = [
  {
    title: "Frontend and backend",
    detail: "Next.js frontend with a TypeScript client and a FastAPI review-support API.",
  },
  {
    title: "Document storage",
    detail: "Durable storage abstraction with PDF page indexing.",
  },
  {
    title: "Evidence retrieval",
    detail: "Deterministic, page-level evidence retrieval and citations.",
  },
  {
    title: "Access control and audit",
    detail: "Project access by organization and role, with audit attribution.",
  },
  {
    title: "Operational dashboard",
    detail: "Reviewer dashboard, reviewer queue, and workload metrics.",
  },
  {
    title: "Diagnostics",
    detail: "Deployment status and backend diagnostics, live AI calls disabled by default.",
  },
];

// Important links kept reachable from the guided demo journey section. CAD
// Intake parses real DXF files and stays reachable as a demo-specific route.
const journeyLinks: { href: string; label: string }[] = [
  { href: "/start-here", label: "Start Here" },
  { href: "/guided-demo", label: "Guided Demo" },
  { href: "/projects", label: "Projects" },
  { href: "/dashboard", label: "Reviewer Dashboard" },
  { href: "/dashboard/queue", label: "Reviewer Queue" },
  { href: "/rule-packs", label: "Rule Packs" },
  { href: "/cad-intake", label: "CAD Intake (DXF)" },
  { href: "/deployment-status", label: "Deployment Status" },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero: concise text on the left, large hero media on the right. */}
      <section className="relative overflow-hidden border-b border-slate-200 bg-white">
        <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-10 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <div>
              <span className="chip chip-brand">
                Municipal stormwater review support
              </span>
              <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
                Civil Engineer AI
              </h1>
              <p className="mt-3 text-xl font-semibold text-water-700">
                A document-first, evidence-first, reviewer-controlled stormwater
                review-support platform
              </p>
              <p className="mt-4 max-w-xl text-lg leading-relaxed text-slate-600">
                Built for municipal and civil engineering plan review. Reviewers
                organize documents, cite page-level evidence, and track findings
                from intake to a reviewer response package.
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                {heroCtas.map((cta, idx) => (
                  <Link
                    key={cta.href + cta.label}
                    href={cta.href}
                    className={`btn ${idx === 0 ? "btn-primary" : "btn-secondary"}`}
                  >
                    {cta.label}
                  </Link>
                ))}
              </div>

              <div className="mt-6">
                <SafetyBoundaryBanner variant="compact" />
              </div>
              <div className="mt-3">
                <BackendStatusBanner />
              </div>
            </div>

            <MarketingMedia
              src={marketingMedia.hero.src}
              alt={marketingMedia.hero.alt}
              variant="hero"
              priority
              label="Hero visual placeholder"
            />
          </div>
        </div>
      </section>

      {/* Brookside Meadows sample project */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="surface-card border-amber-200 bg-amber-50/40 p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="max-w-2xl">
              <span className="chip chip-neutral">Public guided demo</span>
              <h2 className="section-title mt-3">
                Brookside Meadows sample project
              </h2>
              <p className="mt-2 text-slate-600">
                A synthetic subdivision used to show the review-support workflow
                with seeded review-support data. It is not a real submission and
                does not represent a real engineering outcome.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 sm:shrink-0">
              <Link href="/start-here" className="btn btn-primary btn-sm">
                Start Here
              </Link>
              <Link href="/guided-demo" className="btn btn-secondary btn-sm">
                Open the guided demo
              </Link>
            </div>
          </div>
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
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
        </div>
      </section>

      {/* Reviewer workflow */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <h2 className="section-title">Reviewer workflow</h2>
          <p className="section-description">
            From document intake to a reviewer response package. Every step is
            review-support only and keeps a human reviewer responsible.
          </p>
          <div className="mt-6 grid gap-8 lg:grid-cols-[1.1fr_1fr] lg:items-center">
            <MarketingMedia
              src={marketingMedia.workflow.src}
              alt={marketingMedia.workflow.alt}
              variant="wide"
              label="Workflow visual placeholder"
            />
            <div className="grid gap-4 sm:grid-cols-2">
              {workflowCards.map((card) => (
                <Link
                  key={card.title}
                  href={card.href}
                  className="interactive-card flex h-full flex-col p-5"
                >
                  <span className="text-sm font-semibold text-slate-900">
                    {card.title}
                  </span>
                  <p className="mt-1 text-xs text-slate-600">{card.detail}</p>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Technical foundation */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <h2 className="section-title">Technical foundation</h2>
        <p className="section-description">
          A controlled review workflow built on real structure, not a free-form
          chatbot.
        </p>
        <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
          <div className="grid gap-4 sm:grid-cols-2">
            {foundationCards.map((card) => (
              <div key={card.title} className="surface-card p-5">
                <h3 className="text-sm font-semibold text-slate-900">
                  {card.title}
                </h3>
                <p className="mt-1 text-xs text-slate-600">{card.detail}</p>
              </div>
            ))}
          </div>
          <MarketingMedia
            src={marketingMedia.technicalFoundation.src}
            alt={marketingMedia.technicalFoundation.alt}
            variant="wide"
            label="Technical foundation placeholder"
          />
        </div>
      </section>

      {/* Human reviewer boundary */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <MarketingMedia
              src={marketingMedia.humanReviewBoundary.src}
              alt={marketingMedia.humanReviewBoundary.alt}
              variant="panel"
              label="Human review placeholder"
            />
            <div>
              <h2 className="section-title">Human reviewer boundary</h2>
              <p className="section-description">
                Civil Engineer AI assists review. The reviewer stays
                responsible, and every finding needs reviewer confirmation.
              </p>
              <div className="mt-6">
                <SafetyBoundaryBanner />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Guided demo journey */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="surface-card p-6">
          <div className="grid gap-8 lg:grid-cols-[1.1fr_1fr] lg:items-center">
            <MarketingMedia
              src={marketingMedia.guidedDemoJourney.src}
              alt={marketingMedia.guidedDemoJourney.alt}
              variant="wide"
              label="Guided demo placeholder"
            />
            <div>
              <h2 className="section-title">Guided demo journey</h2>
              <p className="section-description">
                Start Here gives the fastest overview and a recommended demo path
                through the Brookside Meadows sample project. The Guided Demo then
                follows one concern end to end.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link href="/start-here" className="btn btn-primary">
                  Start the demo
                </Link>
                <Link href="/guided-demo" className="btn btn-secondary">
                  See the Guided Demo
                </Link>
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                {journeyLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="nav-link border border-slate-200 bg-white"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
