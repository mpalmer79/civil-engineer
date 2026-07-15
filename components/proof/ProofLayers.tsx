import { proofResult } from "@/lib/proof/data";

// F. Layer classification: every extracted layer with its entity count,
// category, rule, and confidence, read from the artifact.
export default function ProofLayers() {
  return (
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
        taxonomy now classifies them with the rule and confidence shown. Three
        layers are intentionally unclassifiable and stay visible as unknown
        for reviewer categorization. A category is a routing aid, not a
        statement that the layer content is correct.
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
  );
}
