import { validateProofResult } from "@/lib/proof/data";

// Integrity gate: validateProofResult re-checks the artifact's own
// ground-truth checks and cross-checks the headline counts. When the artifact
// and the displayed metrics disagree, this section renders a visible alert
// instead of letting the page present unsupported numbers.
export default function ProofIntegrityAlert() {
  const validation = validateProofResult();
  if (validation.ok) return null;

  return (
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
          The structured test artifact and the metrics on this page disagree,
          so the results are not being shown as proven. Each problem needs
          follow-up:
        </p>
        <ul className="mt-3 list-disc pl-5 text-sm text-red-800">
          {validation.problems.map((problem) => (
            <li key={problem}>{problem}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
