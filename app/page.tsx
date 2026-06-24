import Link from "next/link";
import HeroMap from "@/components/HeroMap";
import MetricCard from "@/components/MetricCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import SectionCard from "@/components/SectionCard";
import { getHotspots, projectMetrics } from "@/lib/api";

const heroCtas = [
  { href: "/cad-intake", label: "CAD Intake" },
  { href: "/response-package", label: "Response Package" },
  { href: "/workflow-board", label: "Workflow Board" },
  { href: "/review-packet", label: "Review Packet" },
  { href: "/sheet-viewer", label: "Sheet Viewer" },
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

export default async function HomePage() {
  const hotspots = await getHotspots();
  return (
    <div>
      {/* Hero */}
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <div>
              <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
                Phase 11 · Real CAD File Intake and DXF Parsing Foundation
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

            <HeroMap hotspots={hotspots} />
          </div>
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
            retrieval, human review, auditability, and evaluation, not a
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

      {/* Evidence-first review */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="surface-card p-6">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Evidence-first review
          </h2>
          <p className="mt-3 max-w-3xl text-slate-600">
            Phase 3 adds source chunks and keyword retrieval so every
            review-support finding can trace back to specific pages and sections
            of the submitted documents. Each finding lists the evidence behind
            it, the role that evidence plays (supports, missing, conflict, or
            context), and a note that the finding still needs reviewer
            confirmation.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              Findings link to source excerpts with document and page
              references.
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              Checklist items expand to show the seeded chunks linked to them.
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              Retrieval is keyword and metadata based; embeddings and semantic
              retrieval come later.
            </div>
          </div>
          <p className="mt-5 max-w-3xl text-slate-600">
            Phase 4 adds controlled AI draft findings: for each checklist item the
            backend retrieves evidence, builds a constrained prompt, validates the
            structured output, runs safety checks, and saves a draft finding that
            requires human review. See the{" "}
            <a
              href="/ai-review"
              className="font-semibold text-water-700 hover:text-water-600"
            >
              AI Review
            </a>{" "}
            page.
          </p>
        </div>
      </section>

      {/* Phase 5: human review and evaluation scoring */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="surface-card p-6">
          <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
            Phase 5
          </span>
          <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
            Human review and evaluation scoring
          </h2>
          <p className="mt-3 max-w-3xl text-slate-600">
            Civil Engineer AI now tracks reviewer actions and compares AI draft
            findings against the expected review issues. A reviewer can accept,
            edit, reject, escalate, mark unclear, or request more information on
            each draft finding, and every action records a status transition and
            an audit event. Evaluation scoring then measures recall, precision,
            citation validity, and quality signals against the expected findings.
            No action approves or certifies the work.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              The{" "}
              <a
                href="/human-review"
                className="font-semibold text-water-700 hover:text-water-600"
              >
                Human Review
              </a>{" "}
              queue records persisted reviewer actions and status transitions.
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              The{" "}
              <a
                href="/evaluation"
                className="font-semibold text-water-700 hover:text-water-600"
              >
                Evaluation
              </a>{" "}
              dashboard scores a review run and stores recall and precision
              metrics.
            </div>
          </div>
        </div>
      </section>

      {/* Phase 6: plan sheet and CAD-aware review foundation */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="surface-card p-6">
            <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
              Phase 6
            </span>
            <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
              Plan sheet and CAD-aware review foundation
            </h2>
            <p className="mt-3 max-w-3xl text-slate-600">
              Civil Engineer AI now connects document findings to a plan sheet
              index, CAD-aware civil feature metadata, plan references, missing
              sheet detection, and plan consistency findings. The CAD-aware
              metadata is seeded, not extracted from real CAD files, and the
              system does not parse DWG or DXF drawings, verify CAD, or perform
              final design review. This phase prepares for a future Autodesk and
              CAD integration path while keeping every finding under human
              review.
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                The{" "}
                <a
                  href="/plan-sheets"
                  className="font-semibold text-water-700 hover:text-water-600"
                >
                  Plan Sheets
                </a>{" "}
                page shows the Brookside Meadows plan sheet index with revisions
                and missing sheet detection.
              </div>
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                The{" "}
                <a
                  href="/cad-review"
                  className="font-semibold text-water-700 hover:text-water-600"
                >
                  CAD Review
                </a>{" "}
                page shows CAD-aware feature metadata, plan references, and plan
                consistency findings.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Phase 7: plan sheet viewer and sheet hotspot review */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="surface-card p-6">
          <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
            Phase 7
          </span>
          <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
            Plan sheet viewer and sheet hotspot review
          </h2>
          <p className="mt-3 max-w-3xl text-slate-600">
            A reviewer can now open a plan sheet, see seeded visual hotspots over
            a synthetic sheet preview, and inspect the connected plan references,
            CAD-aware metadata, documents, checklist items, and plan consistency
            findings in place. Reviewers record review-support actions on plan
            consistency findings. The sheet preview and hotspots are seeded
            review-support metadata, not parsed PDF, DWG, DXF, or Autodesk data,
            and nothing here verifies CAD, certifies compliance, or replaces a
            licensed engineer.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              The{" "}
              <a
                href="/sheet-viewer"
                className="font-semibold text-water-700 hover:text-water-600"
              >
                Sheet Viewer
              </a>{" "}
              opens a Brookside Meadows sheet with seeded hotspot annotations.
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              Each hotspot links to plan consistency findings a reviewer can
              mark needs follow up, reviewer confirmed, not applicable, or needs
              more information.
            </div>
          </div>
        </div>
      </section>

      {/* Phase 8: review packet builder and evidence traceability */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="surface-card p-6">
          <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
            Phase 8
          </span>
          <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
            Review packet builder and evidence traceability
          </h2>
          <p className="mt-3 max-w-3xl text-slate-600">
            A reviewer can now generate a Brookside Meadows review-support packet
            draft that assembles documents, checklist items, findings, plan
            sheets, CAD-aware metadata, hotspots, plan consistency findings,
            human review actions, and audit evidence into structured sections.
            Each packet item links back to its source evidence, an evidence
            traceability matrix shows the links row by row, and a printable
            review-support summary is available. The packet is a draft that does
            not approve plans, certify compliance, stamp drawings, verify CAD,
            or validate the design.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              The{" "}
              <a
                href="/review-packet"
                className="font-semibold text-water-700 hover:text-water-600"
              >
                Review Packet
              </a>{" "}
              page generates the packet, groups issues into sections, and shows
              the traceability matrix.
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              Reviewers record actions on packet items and open a printable draft
              review-support summary.
            </div>
          </div>
        </div>
      </section>

      {/* Phase 9: reviewer workflow board and issue resolution tracking */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="surface-card p-6">
            <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
              Phase 9
            </span>
            <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
              Reviewer workflow board and issue resolution tracking
            </h2>
            <p className="mt-3 max-w-3xl text-slate-600">
              A reviewer can now promote the review packet items into an
              operational workflow board. Each item moves through triage,
              follow-up, more information requests, reviewer checked, and ready
              for handoff, with every status transition, reviewer note, and
              follow-up request recorded and audited. Ready for handoff means
              the organized review-support evidence is ready to hand to a
              licensed Professional Engineer. The board does not approve plans,
              certify compliance, stamp drawings, verify CAD, or validate the
              design, and there is no approve action.
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                The{" "}
                <a
                  href="/workflow-board"
                  className="font-semibold text-water-700 hover:text-water-600"
                >
                  Workflow Board
                </a>{" "}
                page groups items into workflow columns and tracks each item
                from triage to handoff.
              </div>
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                Reviewers open follow-up requests, record notes, and review the
                ready-for-handoff summary, all under human control.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Phase 10: external review response package */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="surface-card p-6">
          <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
            Phase 10
          </span>
          <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
            External review response package
          </h2>
          <p className="mt-3 max-w-3xl text-slate-600">
            A reviewer can now turn the ready-for-handoff workflow items into a
            structured draft external response package for an applicant, design
            engineer, municipal reviewer, or internal review team. The package
            groups items by topic, drafts plain review-support wording, keeps
            traceability to the workflow item, packet item, and source evidence,
            and adds an attachment checklist, a printable draft, a package
            history, and a human review sign-off checklist. The package is draft
            external communication support. It does not send email, approve
            plans, certify compliance, stamp drawings, verify CAD, or validate
            the design, and there is no approve action.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              The{" "}
              <a
                href="/response-package"
                className="font-semibold text-water-700 hover:text-water-600"
              >
                Response Package
              </a>{" "}
              page generates the draft, groups items into sections, and lets a
              reviewer edit draft wording and manage statuses.
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              The real workflow runs review packet, workflow board, response
              package, then human review. Civil Engineer AI never issues the
              response itself.
            </div>
          </div>
        </div>
      </section>

      {/* Phase 11: real CAD file intake and DXF parsing foundation */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="surface-card p-6">
            <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
              Phase 11
            </span>
            <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
              Real CAD file intake and DXF parsing foundation
            </h2>
            <p className="mt-3 max-w-3xl text-slate-600">
              Civil Engineer AI now parses a real DXF file. It extracts layers,
              entities, blocks, and text, detects sheet references, detail
              references, pipe, basin, outfall, and wetland buffer labels with
              confidence labels, compares extracted references against the
              seeded plan sheets, and raises review-support findings for missing
              matches, unclear details, possible label conflicts, and
              uncategorized layers. Findings can become workflow items. This is
              DXF metadata extraction only. It does not verify CAD, validate
              geometry or design, certify compliance, approve plans, or replace
              a licensed Professional Engineer. DXF is the only supported file
              type; DWG, Autodesk, OCR, and GIS remain future work.
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                The{" "}
                <a
                  href="/cad-intake"
                  className="font-semibold text-water-700 hover:text-water-600"
                >
                  CAD Intake
                </a>{" "}
                page parses the bundled Brookside Meadows sample DXF and shows
                the extracted metadata and findings.
              </div>
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                Browser DXF upload is a later enhancement. This phase uses safe
                backend fixture-based parsing with real DXF extraction.
              </div>
            </div>
          </div>
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
