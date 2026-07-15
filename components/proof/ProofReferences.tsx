import { proofResult } from "@/lib/proof/data";

// E. Reference evidence: sheet and detail callouts extracted from the drawing
// and compared against the seeded plan-sheet index.

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

export default function ProofReferences() {
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
  );
}
