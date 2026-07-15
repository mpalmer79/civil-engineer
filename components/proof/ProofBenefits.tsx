import { workflowBenefits } from "@/components/proof/content";

// J. What the validated capabilities mean for a civil review team.
export default function ProofBenefits() {
  return (
    <section
      aria-labelledby="poc-benefits-heading"
      className="border-t border-slate-100 bg-slate-50"
    >
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2
          id="poc-benefits-heading"
          className="text-2xl font-bold tracking-tight text-slate-950"
        >
          What this means for a review team
        </h2>
        <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workflowBenefits.map((benefit) => (
            <li
              key={benefit.title}
              className="rounded-lg border border-slate-200 bg-white p-5"
            >
              <h3 className="text-sm font-semibold text-slate-900">
                {benefit.title}
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-slate-600">
                {benefit.detail}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
