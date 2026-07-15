import Link from "next/link";

// The closing call to action into the guided demo.
export default function FinalCta() {
  return (
    <section aria-labelledby="final-cta-heading" className="bg-slate-900">
      <div className="mx-auto max-w-6xl px-4 py-12 text-center sm:px-6 lg:px-8">
        <h2 id="final-cta-heading" className="text-xl font-semibold text-white">
          See one concern traced from document to handoff
        </h2>

        <p className="mx-auto mt-2 max-w-2xl text-sm text-slate-300">
          The guided demo walks the Brookside Meadows review in about five
          minutes: intake, evidence, checklist, applicant response, and
          reviewer-controlled handoff.
        </p>

        <div className="mt-6">
          <Link
            href="/guided-demo"
            className="inline-block rounded-lg bg-water-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-water-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            Start the Guided Demo
          </Link>
        </div>
      </div>
    </section>
  );
}
