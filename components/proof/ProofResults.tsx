import { proofResult } from "@/lib/proof/data";

// D. Reviewer-checked results: the headline metric tiles, every value read
// from the structured test artifact.
export default function ProofResults() {
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

  return (
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
        declares its units as {proofResult.drawing_units}; units are read from
        the DXF header, never assumed. Parser: {proofResult.parser.name}{" "}
        {proofResult.parser.version}.
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
  );
}
