import Link from "next/link";
import type { Metadata } from "next";

import {
  formatBytes,
  proofManifest,
  proofResult,
  validateProofResult,
} from "@/lib/proof/data";

// Public proof-of-concept page. Every metric on this page is read from the
// generated structured test result and the artifact manifest; nothing is
// hardcoded separately from the evidence. validateProofResult() re-checks the
// artifact's own ground-truth checks and the page fails visibly when the
// artifact and the displayed metrics disagree.

export const metadata: Metadata = {
  title: "Proof of Concept: DXF Intake and Review Support | Civil Engineer AI",
  description:
    "Reproducible DXF proof of concept: deterministic CAD metadata extraction, reference identification, and stormwater review support over a synthetic Brookside Meadows test drawing.",
};

const provenPoints = [
  "A structurally valid DXF is accepted by the real intake validation",
  "The production ezdxf parser executes against the uploaded file",
  "Entities and layers are inventoried with safe local bounds",
  "Text, blocks, and drawing units are extracted",
  "Sheet and detail references are identified and matched against the plan-sheet index",
  "Results persist to the database and are retrieved through reviewer-facing endpoints",
  "Review-support findings come from deterministic rules",
  "The artifacts regenerate byte-identically from the committed scripts",
] as const;

const notProvenPoints = [
  "Correct basin sizing",
  "Correct pipe slope",
  "Adequate hydraulic capacity",
  "Correct grading",
  "Regulatory compliance",
  "Construction readiness",
  "Design safety",
  "Final plan approval",
  "Survey accuracy",
  "Complete CAD semantic understanding",
] as const;

const workflowBenefits = [
  {
    title: "Faster drawing inventory",
    detail:
      "A reviewer sees every layer, block, and annotation within seconds of upload instead of opening the file and panning through it.",
  },
  {
    title: "Early missing-reference identification",
    detail:
      "Sheet callouts that point at sheets absent from the submission surface before a reviewer has read a single page.",
  },
  {
    title: "Layer organization at a glance",
    detail:
      "The taxonomy sorts layers into review categories with the rule and confidence shown, and unknown layers stay visible for reviewer categorization.",
  },
  {
    title: "Searchable plan annotations",
    detail:
      "Extracted text is normalized and stored, so labels and notes become searchable evidence rather than pixels.",
  },
  {
    title: "Consistent review preparation",
    detail:
      "Every submission passes the same deterministic checks, so preparation quality does not depend on who picks up the file.",
  },
  {
    title: "Stronger reviewer handoff",
    detail:
      "Findings carry their evidence, rule, and confidence, and every one requires human review. Engineering judgment stays with the licensed reviewer.",
  },
] as const;

const nextImprovements = [
  "Configurable per-organization and per-project layer taxonomy overrides with an audit trail",
  "Typed facility identity persisted with the parse run rather than derived at parse time",
  "Broader geometry support, including exact envelopes where only safe overestimates exist today",
  "Reference parsing across more callout conventions without overmatching",
  "A larger DXF evaluation corpus covering more drafting styles",
  "Browser-level upload validation before bytes leave the reviewer's machine",
  "Documented performance limits over large drawings",
  "Additional civil drawing conventions beyond subdivision stormwater plans",
] as const;

function matchStateLabel(state: string): string {
  switch (state) {
    case "matched":
      return "Matched";
    case "missing":
      return "No match found";
    case "ambiguous":
      return "Ambiguous, needs human review";
    default:
      return "Extracted label";
  }
}

function matchStateClasses(state: string): string {
  switch (state) {
    case "matched":
      return "bg-slate-100 text-slate-700";
    case "missing":
      return "bg-amber-50 text-amber-800";
    case "ambiguous":
      return "bg-amber-50 text-amber-800";
    default:
      return "bg-slate-50 text-slate-600";
  }
}

export default function ProofOfConceptPage() {
  const validation = validateProofResult();
  const counts = proofResult.counts;

  const metricTiles = [
    { label: "Upload HTTP result", value: String(proofResult.intake.upload_http_status) },
    { label: "Intake validation", value: proofResult.intake.validation_status },
    { label: "Parse status", value: proofResult.intake.parse_status },
    { label: "Entities", value: String(counts.entities) },
    { label: "Layers", value: String(counts.layers) },
    { label: "Blocks", value: String(counts.blocks) },
    { label: "Text records", value: String(counts.text_records) },
    { label: "Reference candidates", value: String(counts.reference_candidates) },
    { label: "Review-support findings", value: String(counts.findings) },
    { label: "Matched references", value: String(counts.matched_references) },
    {
      label: "Missing or ambiguous references",
      value: String(counts.missing_or_ambiguous_references),
    },
  ] as const;

  const sheetAndDetailReferences = proofResult.references.filter(
    (reference) =>
      reference.reference_type === "sheet_reference" ||
      reference.reference_type === "detail_reference",
  );
  const extractedLabels = proofResult.references.filter(
    (reference) =>
      reference.reference_type !== "sheet_reference" &&
      reference.reference_type !== "detail_reference",
  );

  return (
    <div className="bg-white text-slate-900">
      {/* A. Hero */}
      <section
        aria-labelledby="poc-hero-heading"
        className="border-b border-slate-100 bg-gradient-to-b from-slate-50 to-white"
      >
        <div className="mx-auto max-w-6xl px-4 pb-12 pt-12 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-xs font-semibold uppercase tracking-wider text-water-700">
              Technical validation report
            </p>
            <h1
              id="poc-hero-heading"
              className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl"
            >
              Proof of Concept: DXF Intake and Review Support
            </h1>
            <p className="mt-4 text-base leading-relaxed text-slate-600">
              A synthetic, structurally valid civil-site DXF was processed
              through the real Civil Engineer AI upload and parse services.
              The results below demonstrate deterministic DXF metadata
              extraction, consistency checking, reference identification, and
              reviewer-support analysis. They do not demonstrate engineering
              approval or design correctness.
            </p>
            <p className="mt-3 text-sm text-slate-500">
              The drawing is synthetic. It is not a real survey, not a real
              submission, and not suitable for construction. Snapshot{" "}
              <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-700">
                {proofResult.snapshot_id}
              </code>
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <a
                href="#poc-results-heading"
                className="rounded-lg bg-water-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-water-800"
              >
                Explore the results
              </a>
              {/* These anchors hit a route handler that streams a file
                  download, not a page, so next/link does not apply. */}
              {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
              <a
                href="/api/proof-of-concept/download/proof-bundle"
                className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Download the test bundle
              </a>
              {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
              <a
                href="/api/proof-of-concept/download/proof-report"
                className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                View the integration report
              </a>
            </div>
          </div>
        </div>
      </section>

      {!validation.ok ? (
        <section
          aria-labelledby="poc-integrity-heading"
          className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8"
        >
          <div
            role="alert"
            className="rounded-xl border border-red-300 bg-red-50 p-6"
          >
            <h2
              id="poc-integrity-heading"
              className="text-lg font-semibold text-red-900"
            >
              Proof artifact consistency check failed
            </h2>
            <p className="mt-2 text-sm text-red-800">
              The structured test artifact and the metrics on this page
              disagree, so the results are not being shown as proven. Each
              problem needs follow-up:
            </p>
            <ul className="mt-3 list-disc pl-5 text-sm text-red-800">
              {validation.problems.map((problem) => (
                <li key={problem}>{problem}</li>
              ))}
            </ul>
          </div>
        </section>
      ) : null}

      {/* B. What was tested */}
      <section
        aria-labelledby="poc-tested-heading"
        className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"
      >
        <h2
          id="poc-tested-heading"
          className="text-2xl font-bold tracking-tight text-slate-950"
        >
          What was tested
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
          The test drawing is a conceptual subdivision plan for the synthetic
          Brookside Meadows case study in the Town of Hartwell. It was
          generated by a committed script so anyone can rebuild the exact same
          file. The geometry is conceptual: no surveyed accuracy is implied.
        </p>
        <ul className="mt-6 grid gap-3 text-sm text-slate-700 sm:grid-cols-2 lg:grid-cols-3">
          {[
            "47 conceptual lots with lot number labels",
            "Road alignment with a cul-de-sac",
            "Grading contours with elevation labels",
            "Wetland boundary and 50 ft buffer",
            "Detention and infiltration facilities",
            "Storm pipes and an outfall",
            "Erosion and sediment controls",
            "Utility corridors",
            "Sheet references, including one intentionally missing sheet",
            "Detail references, including one intentionally ambiguous callout",
            "Facility labels that intentionally share numbers across types",
            "Five reusable CAD blocks and a paper-space title layout",
          ].map((item) => (
            <li
              key={item}
              className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3"
            >
              {item}
            </li>
          ))}
        </ul>
      </section>

      {/* C. Actual pipeline */}
      <section
        aria-labelledby="poc-pipeline-heading"
        className="border-t border-slate-100 bg-slate-50"
      >
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2
            id="poc-pipeline-heading"
            className="text-2xl font-bold tracking-tight text-slate-950"
          >
            The actual pipeline
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
            The proof harness talks to the same routes the browser uses. No
            test-only shortcut bypasses the production parser. Each stage
            names its application boundary and repository module.
          </p>
          <ol className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {proofResult.pipeline.map((stage, index) => (
              <li
                key={stage.stage}
                className="rounded-lg border border-slate-200 bg-white p-4"
              >
                <p className="text-xs font-semibold uppercase tracking-wider text-water-700">
                  Stage {index + 1}
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-900">
                  {stage.stage}
                </p>
                <p className="mt-1 text-xs text-slate-500">{stage.boundary}</p>
                <p className="mt-1 break-all font-mono text-xs text-slate-500">
                  {stage.module}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* D. Verified results */}
      <section
        aria-labelledby="poc-results-heading"
        className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"
      >
        <h2
          id="poc-results-heading"
          className="text-2xl font-bold tracking-tight text-slate-950"
        >
          Reviewer-checked results
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
          Every value below is read from the structured test artifact, which
          records {proofResult.checks.length} ground-truth checks. The drawing
          declares its units as {proofResult.drawing_units}; units are read
          from the DXF header, never assumed. Parser:{" "}
          {proofResult.parser.name} {proofResult.parser.version}.
        </p>
        <dl className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {metricTiles.map((tile) => (
            <div
              key={tile.label}
              className="rounded-lg border border-slate-200 bg-white p-4"
            >
              <dt className="text-xs font-medium text-slate-500">
                {tile.label}
              </dt>
              <dd className="mt-1 text-xl font-bold text-slate-950">
                {tile.value}
              </dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 text-xs text-slate-500">
          Entity types extracted:{" "}
          {Object.entries(proofResult.entity_types)
            .map(([type, count]) => `${type} (${count})`)
            .join(", ")}
          .
        </p>
      </section>

      {/* E. Reference evidence */}
      <section
        aria-labelledby="poc-references-heading"
        className="border-t border-slate-100 bg-slate-50"
      >
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2
            id="poc-references-heading"
            className="text-2xl font-bold tracking-tight text-slate-950"
          >
            Reference evidence
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
            Sheet and detail callouts extracted from the drawing and compared
            against the seeded plan-sheet index. A matched reference means the
            text matched an indexed sheet record. It is not an engineering
            verification of the referenced content.
          </p>
          <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <caption className="sr-only">
                Sheet and detail references with match state and reason
              </caption>
              <thead>
                <tr className="text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <th scope="col" className="px-4 py-3">
                    Extracted text
                  </th>
                  <th scope="col" className="px-4 py-3">
                    Normalized
                  </th>
                  <th scope="col" className="px-4 py-3">
                    Type
                  </th>
                  <th scope="col" className="px-4 py-3">
                    Match state
                  </th>
                  <th scope="col" className="px-4 py-3">
                    Reason
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sheetAndDetailReferences.map((reference) => (
                  <tr key={`${reference.reference_type}-${reference.reference_text}`}>
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">
                      {reference.reference_text}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">
                      {reference.normalized_reference}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600">
                      {reference.reference_type.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${matchStateClasses(reference.match_state)}`}
                      >
                        {matchStateLabel(reference.match_state)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600">
                      {reference.match_reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-xs text-slate-500">
            {extractedLabels.length} additional labels (facility, outfall, and
            wetland buffer text) were extracted for reviewer confirmation.
          </p>
        </div>
      </section>

      {/* F. Layer classification */}
      <section
        aria-labelledby="poc-layers-heading"
        className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"
      >
        <h2
          id="poc-layers-heading"
          className="text-2xl font-bold tracking-tight text-slate-950"
        >
          Layer classification
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
          An earlier taxonomy over-flagged common civil layers such as C-PROP,
          C-ROAD, C-LOTS, C-LABEL, and C-LANDSCAPE as unknown. The data-driven
          taxonomy now classifies them with the rule and confidence shown.
          Three layers are intentionally unclassifiable and stay visible as
          unknown for reviewer categorization. A category is a routing aid,
          not a statement that the layer content is correct.
        </p>
        <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <caption className="sr-only">
              Extracted layers with entity counts and classification
            </caption>
            <thead>
              <tr className="text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                <th scope="col" className="px-4 py-3">
                  Layer
                </th>
                <th scope="col" className="px-4 py-3">
                  Entities
                </th>
                <th scope="col" className="px-4 py-3">
                  Category
                </th>
                <th scope="col" className="px-4 py-3">
                  Rule
                </th>
                <th scope="col" className="px-4 py-3">
                  Confidence
                </th>
                <th scope="col" className="px-4 py-3">
                  Explanation
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {proofResult.layers.map((layer) => (
                <tr key={layer.layer_name}>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">
                    {layer.layer_name}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    {layer.entity_count}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        layer.category === "unknown"
                          ? "bg-amber-50 text-amber-800"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {layer.category.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    {layer.classification_rule.rule_kind}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    {layer.classification_rule.confidence}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    {layer.classification_rule.explanation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* G. Review-support findings */}
      <section
        aria-labelledby="poc-findings-heading"
        className="border-t border-slate-100 bg-slate-50"
      >
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2
            id="poc-findings-heading"
            className="text-2xl font-bold tracking-tight text-slate-950"
          >
            Review-support findings
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
            Every finding below came from a deterministic rule, carries its
            evidence, and requires human review. None of them is a violation
            determination: that judgment belongs to a licensed reviewer
            through an authorized workflow. Note what is absent: DETENTION
            BASIN 1 and INFILTRATION BASIN 1 share the number 1 but are
            different facility types, so the parser no longer pairs them as a
            conflict.
          </p>
          <ul className="mt-6 grid gap-4 lg:grid-cols-2">
            {proofResult.findings.map((finding) => (
              <li
                key={finding.title}
                className="rounded-lg border border-slate-200 bg-white p-5"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                    {finding.finding_type.replace(/_/g, " ")}
                  </span>
                  <span className="inline-flex rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">
                    attention: {finding.severity}
                  </span>
                  <span className="inline-flex rounded-full bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-600">
                    deterministic rule
                  </span>
                </div>
                <h3 className="mt-3 text-sm font-semibold text-slate-900">
                  {finding.title}
                </h3>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">
                  {finding.description}
                </p>
                <p className="mt-2 text-xs font-medium text-water-700">
                  Reviewer action: confirm or dismiss with project context.
                </p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* H and I. What this proves and does not prove */}
      <section
        aria-labelledby="poc-proves-heading"
        className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"
      >
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <h2
              id="poc-proves-heading"
              className="text-xl font-bold tracking-tight text-slate-950"
            >
              What this proves
            </h2>
            <ul className="mt-4 space-y-2 text-sm text-slate-700">
              {provenPoints.map((point) => (
                <li key={point} className="flex gap-2">
                  <span aria-hidden="true" className="text-water-700">
                    +
                  </span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
            <h2 className="text-xl font-bold tracking-tight text-slate-950">
              What this does not prove
            </h2>
            <p className="mt-2 text-xs text-amber-800">
              These determinations belong to a licensed Professional Engineer
              and were not attempted:
            </p>
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {notProvenPoints.map((point) => (
                <li key={point} className="flex gap-2">
                  <span aria-hidden="true" className="text-amber-700">
                    -
                  </span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* J. Civil engineering benefits */}
      <section
        aria-labelledby="poc-benefits-heading"
        className="border-t border-slate-100 bg-slate-50"
      >
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2
            id="poc-benefits-heading"
            className="text-2xl font-bold tracking-tight text-slate-950"
          >
            What this means for a review team
          </h2>
          <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workflowBenefits.map((benefit) => (
              <li
                key={benefit.title}
                className="rounded-lg border border-slate-200 bg-white p-5"
              >
                <h3 className="text-sm font-semibold text-slate-900">
                  {benefit.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-600">
                  {benefit.detail}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* K. Reproducibility */}
      <section
        aria-labelledby="poc-repro-heading"
        className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"
      >
        <h2
          id="poc-repro-heading"
          className="text-2xl font-bold tracking-tight text-slate-950"
        >
          Reproducibility
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
          The proof does not depend on manually copied files. Two committed
          scripts rebuild everything on this page, and continuous integration
          regenerates the artifacts and fails if they drift from the committed
          bytes.
        </p>
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="text-sm font-semibold text-slate-900">
              Rebuild the proof
            </h3>
            <pre className="mt-3 overflow-x-auto rounded bg-slate-900 p-4 text-xs text-slate-100">
              <code>
                {`python scripts/generate_brookside_proof_dxf.py
python scripts/run_dxf_proof.py`}
              </code>
            </pre>
            <p className="mt-3 text-xs text-slate-500">
              Requirements: Python 3.12, the backend requirements file, and
              nothing else. No API keys, no external services. Fixture
              version: {proofResult.fixture_version}.
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="text-sm font-semibold text-slate-900">
              Where the logic lives
            </h3>
            <ul className="mt-3 space-y-1 font-mono text-xs text-slate-600">
              <li>scripts/generate_brookside_proof_dxf.py</li>
              <li>scripts/run_dxf_proof.py</li>
              <li>scripts/dxf_proof_expected.json</li>
              <li>backend/app/services/cad/layer_taxonomy.py</li>
              <li>backend/app/services/cad/facility_identity.py</li>
              <li>backend/app/services/cad/reference_parser.py</li>
              <li>backend/app/services/cad/geometry.py</li>
              <li>backend/app/services/cad_intake_service.py</li>
            </ul>
          </div>
        </div>
      </section>

      {/* L. Artifact downloads */}
      <section
        aria-labelledby="poc-downloads-heading"
        className="border-t border-slate-100 bg-slate-50"
      >
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2
            id="poc-downloads-heading"
            className="text-2xl font-bold tracking-tight text-slate-950"
          >
            Download the evidence
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
            {proofManifest.synthetic_disclosure}
          </p>
          <ul className="mt-6 grid gap-4 sm:grid-cols-2">
            {proofManifest.artifacts.map((artifact) => (
              <li
                key={artifact.artifact_id}
                className="flex flex-col rounded-lg border border-slate-200 bg-white p-5"
              >
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-slate-900">
                    {artifact.display_name}
                  </h3>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium uppercase text-slate-600">
                    {artifact.file_type}
                  </span>
                </div>
                <p className="mt-2 flex-1 text-xs leading-relaxed text-slate-600">
                  {artifact.description}
                </p>
                <p className="mt-3 text-xs text-slate-500">
                  {formatBytes(artifact.file_size_bytes)}, synthetic data
                </p>
                <p className="mt-1 break-all font-mono text-[10px] text-slate-500">
                  sha256: {artifact.sha256}
                </p>
                <a
                  href={artifact.download_route}
                  className="mt-4 inline-flex w-fit rounded-lg border border-water-700 px-4 py-2 text-xs font-semibold text-water-700 hover:bg-water-50"
                >
                  Download {artifact.filename}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* M. Next improvements */}
      <section
        aria-labelledby="poc-next-heading"
        className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"
      >
        <h2
          id="poc-next-heading"
          className="text-2xl font-bold tracking-tight text-slate-950"
        >
          Known limitations and next improvements
        </h2>
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
            <h3 className="text-sm font-semibold text-slate-900">
              Current limitations, stated plainly
            </h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {proofResult.limitations.map((limitation) => (
                <li key={limitation} className="flex gap-2">
                  <span aria-hidden="true" className="text-amber-700">
                    -
                  </span>
                  {limitation}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <h3 className="text-sm font-semibold text-slate-900">
              The actual roadmap
            </h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {nextImprovements.map((item) => (
                <li key={item} className="flex gap-2">
                  <span aria-hidden="true" className="text-water-700">
                    +
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* N. Calls to action */}
      <section
        aria-labelledby="poc-cta-heading"
        className="border-t border-slate-100 bg-slate-50"
      >
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2
            id="poc-cta-heading"
            className="text-2xl font-bold tracking-tight text-slate-950"
          >
            Keep evaluating
          </h2>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/guided-demo"
              className="rounded-lg bg-water-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-water-800"
            >
              Start the guided demo
            </Link>
            <Link
              href="/start-here"
              className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white"
            >
              Review the technical overview
            </Link>
            <Link
              href="/projects/proj_brookside_meadows"
              className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white"
            >
              Explore Brookside Meadows
            </Link>
            <Link
              href="/projects/proj_brookside_meadows/cad"
              className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white"
            >
              Open DXF intake
            </Link>
            <a
              href="https://github.com/mpalmer79/civil-engineer"
              className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white"
            >
              Review the source-backed methodology
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
