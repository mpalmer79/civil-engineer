import { proofLogicModules } from "@/components/proof/content";
import { proofResult } from "@/lib/proof/data";

// K. Reproducibility: the committed scripts that rebuild every artifact on
// the page, and where the parsing logic lives in the repository.
export default function ProofRepro() {
  return (
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
        The validation does not depend on manually copied files. Two committed
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
            nothing else. No API keys, no external services. Fixture version:{" "}
            {proofResult.fixture_version}.
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h3 className="text-sm font-semibold text-slate-900">
            Where the logic lives
          </h3>
          <ul className="mt-3 space-y-1 font-mono text-xs text-slate-600">
            {proofLogicModules.map((module) => (
              <li key={module}>{module}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
