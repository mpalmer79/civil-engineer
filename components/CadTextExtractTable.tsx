import type { CadTextExtract } from "@/lib/api";

// A table of extracted DXF text values and their detected reference types.
export default function CadTextExtractTable({
  texts,
}: {
  texts: CadTextExtract[];
}) {
  if (texts.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-600">
        No text extracted.
      </div>
    );
  }
  return (
    <div className="surface-card overflow-x-auto p-0">
      <table className="min-w-full divide-y divide-slate-100 text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-slate-600">
            <th className="px-4 py-3">Text</th>
            <th className="px-4 py-3">Reference type</th>
            <th className="px-4 py-3">Layer</th>
            <th className="px-4 py-3">Category</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {texts.map((text) => (
            <tr key={text.textExtractId}>
              <td className="px-4 py-2 font-medium text-slate-800">
                {text.textValue}
              </td>
              <td className="px-4 py-2 text-slate-600">
                {text.referenceType.replace(/_/g, " ")}
              </td>
              <td className="px-4 py-2 text-slate-600">
                {text.layerName ?? "n/a"}
              </td>
              <td className="px-4 py-2 text-slate-600">
                {text.reviewCategory.replace(/_/g, " ")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
