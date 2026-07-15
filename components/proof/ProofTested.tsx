import { testedDrawingContents } from "@/components/proof/content";

// B. What was tested: the synthetic Brookside Meadows test drawing and its
// intentionally planted contents.
export default function ProofTested() {
  return (
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
        Brookside Meadows case study in the Town of Hartwell. It was generated
        by a committed script so anyone can rebuild the exact same file. The
        geometry is conceptual: no surveyed accuracy is implied.
      </p>
      <ul className="mt-6 grid gap-3 text-sm text-slate-700 sm:grid-cols-2 lg:grid-cols-3">
        {testedDrawingContents.map((item) => (
          <li
            key={item}
            className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3"
          >
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}
