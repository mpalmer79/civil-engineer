import Link from "next/link";
import HeroMap from "@/components/HeroMap";
import MetricCard from "@/components/MetricCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import SectionCard from "@/components/SectionCard";
import { projectMetrics } from "@/data/brookside";

const heroCtas = [
  { href: "/project", label: "Project dashboard" },
  { href: "/checklist", label: "Review checklist" },
  { href: "/findings", label: "Findings" },
  { href: "/evaluation", label: "Evaluation" },
];

const metricCards = [
  { value: `${projectMetrics.acreage}`, label: "Site acres", accent: "land" as const },
  { value: projectMetrics.proposedLots, label: "Proposed lots", accent: "land" as const },
  { value: projectMetrics.disturbedAcres, label: "Disturbed acres", accent: "land" as const },
  { value: projectMetrics.documents, label: "Submitted / referenced documents", accent: "water" as const },
  { value: projectMetrics.checklistItems, label: "Stormwater checklist items", accent: "water" as const },
  { value: projectMetrics.plantedIssues, label: "Planted review issues", accent: "amber" as const },
  { value: projectMetrics.evaluationCases, label: "Evaluation cases", accent: "water" as const },
];

const howItWorks = [
  "Review package is loaded",
  "Documents are organized",
  "Checklist items are applied",
  "Evidence is retrieved",
  "Findings are generated",
  "Human reviewer acts",
  "Audit trail is preserved",
  "Evaluation measures performance",
];

const futureModules = [
  "Grading review",
  "Utility coordination",
  "Roadway layout review",
  "Erosion control review",
  "Inspection closeout",
  "RFI resolution",
  "Municipal comment response",
];

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <div>
              <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                Phase 1 · Static portfolio prototype
              </span>
              <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
                Civil Engineer AI
              </h1>
              <p className="mt-2 text-xl font-semibold text-water-700">
                Stormwater Review Assistant
              </p>
              <p className="mt-5 text-lg text-slate-600">
                Evidence-first GenAI review support for stormwater and land
                development workflows.
              </p>
              <p className="mt-4 text-base text-slate-600">
                Civil Engineer AI helps a human reviewer inspect a synthetic
                subdivision package, compare submitted documents against
                stormwater checklist requirements, flag missing or conflicting
                evidence, and track every finding through human review and audit
                history.
              </p>

              <div className="mt-6">
                <SafetyBoundaryBanner variant="compact" />
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                {heroCtas.map((cta, idx) => (
                  <Link
                    key={cta.href}
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

            <HeroMap />
          </div>
        </div>
      </section>

      {/* Metrics */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Brookside Meadows — review fixture at a glance
        </h2>
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-7">
          {metricCards.map((m) => (
            <MetricCard
              key={m.label}
              value={m.value}
              label={m.label}
              accent={m.accent}
            />
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            How it works
          </h2>
          <p className="mt-2 max-w-2xl text-slate-600">
            A controlled review workflow wraps the AI model in structure,
            retrieval, human review, auditability, and evaluation — not a
            free-form chatbot.
          </p>
          <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {howItWorks.map((step, i) => (
              <li key={step} className="surface-card p-5">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-water-50 text-sm font-bold text-water-700">
                  {i + 1}
                </div>
                <p className="mt-3 text-sm font-medium text-slate-800">
                  {step}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Professional boundary */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <SafetyBoundaryBanner />
      </section>

      {/* Future platform */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.4fr] lg:items-center">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                Stormwater is module one
              </h2>
              <p className="mt-3 text-slate-600">
                The same retrieval, checklist, findings, human-review, audit, and
                evaluation backbone extends across the land development lifecycle.
                Brookside Meadows is authored to carry every future module without
                new seed storytelling.
              </p>
              <Link
                href="/project"
                className="mt-5 inline-block text-sm font-semibold text-water-700 hover:text-water-600"
              >
                See why this project is a strong AI review fixture →
              </Link>
            </div>
            <SectionCard title="Planned future modules">
              <ul className="grid gap-3 sm:grid-cols-2">
                {futureModules.map((mod) => (
                  <li
                    key={mod}
                    className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700"
                  >
                    <span aria-hidden="true" className="text-land-600">
                      ◆
                    </span>
                    {mod}
                  </li>
                ))}
              </ul>
            </SectionCard>
          </div>
        </div>
      </section>
    </div>
  );
}
