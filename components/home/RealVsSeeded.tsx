import { realVsSeeded } from "@/components/home/content";

// The honesty section: what is implemented, what is seeded reference data,
// and what is intentionally out of scope.
export default function RealVsSeeded() {
  return (
    <section
      aria-labelledby="real-vs-seeded-heading"
      className="border-b border-slate-100 bg-white"
    >
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2
          id="real-vs-seeded-heading"
          className="text-xl font-semibold text-slate-950"
        >
          What is real and what is seeded
        </h2>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {realVsSeeded.map((item) => (
            <div
              key={item.title}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-card"
            >
              <h3 className="text-sm font-semibold text-slate-900">
                {item.title}
              </h3>

              <p className="mt-2 text-xs leading-relaxed text-slate-600">
                {item.detail}
              </p>
            </div>
          ))}
        </div>

        <p className="mt-4 text-xs text-slate-500">
          The full real-versus-seeded matrix lives in the repository at
          docs/PRODUCT.md, and the technical overview page summarizes
          the architecture behind it.
        </p>
      </div>
    </section>
  );
}
