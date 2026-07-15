import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";

// The professional boundary section. AI provides review support; a licensed
// engineer makes every decision. This section must remain on the homepage.
export default function HumanDecisionBoundary() {
  return (
    <section
      aria-labelledby="boundary-heading"
      className="border-b border-slate-100 bg-slate-50"
    >
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2
          id="boundary-heading"
          className="text-xl font-semibold text-slate-950"
        >
          The human review boundary
        </h2>

        <p className="mt-1 max-w-3xl text-sm text-slate-600">
          AI provides review support. You make the decisions. Every review is
          human. The system organizes evidence and drafts review-support
          findings; it never approves a plan, certifies compliance, or replaces
          a licensed Professional Engineer.
        </p>

        <div className="mt-5">
          <SafetyBoundaryBanner />
        </div>
      </div>
    </section>
  );
}
