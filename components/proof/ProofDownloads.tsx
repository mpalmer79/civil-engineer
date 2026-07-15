import { formatBytes, proofManifest } from "@/lib/proof/data";

// L. Artifact downloads: every artifact from the manifest with its size,
// SHA-256 hash, and streaming download route.
export default function ProofDownloads() {
  return (
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
  );
}
