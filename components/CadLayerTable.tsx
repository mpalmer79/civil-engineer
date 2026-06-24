import type { CadLayerExtract } from "@/lib/api";

// A table of extracted DXF layers and their review categories.
export default function CadLayerTable({
  layers,
}: {
  layers: CadLayerExtract[];
}) {
  if (layers.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        No layers extracted.
      </div>
    );
  }
  return (
    <div className="surface-card overflow-x-auto p-0">
      <table className="min-w-full divide-y divide-slate-100 text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-4 py-3">Layer</th>
            <th className="px-4 py-3">Entities</th>
            <th className="px-4 py-3">Category</th>
            <th className="px-4 py-3">Content</th>
            <th className="px-4 py-3">Review</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {layers.map((layer) => (
            <tr key={layer.layerExtractId}>
              <td className="px-4 py-2 font-medium text-slate-800">
                {layer.layerName}
              </td>
              <td className="px-4 py-2 text-slate-600">{layer.entityCount}</td>
              <td className="px-4 py-2 text-slate-600">
                {layer.reviewCategory.replace(/_/g, " ")}
              </td>
              <td className="px-4 py-2 text-slate-500">
                {[layer.hasText ? "text" : null, layer.hasGeometry ? "geometry" : null]
                  .filter(Boolean)
                  .join(", ") || "none"}
              </td>
              <td className="px-4 py-2">
                {layer.requiresHumanReview ? (
                  <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[11px] text-amber-700">
                    needs review
                  </span>
                ) : (
                  <span className="text-xs text-slate-400">categorized</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
