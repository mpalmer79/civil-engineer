import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import PilotRequestForm from "@/components/PilotRequestForm";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";

// Public design-partner pilot request page. It is reachable without a login and
// is the conversion target for the homepage and guided demo CTAs. The page sets
// honest expectations: it accepts design-partner conversations and follows up
// before requesting any real project files. It makes no approval, certification,
// or compliance claim, and a human reviewer remains responsible for review work.

export const metadata = {
  title: "Start a design-partner pilot",
};

export default function PilotPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Design-partner pilot"
        title="Start a design-partner pilot"
        description="Run Civil Engineer AI against your pre-submittal QA workflow and see whether it can help your team catch review-support issues before the package goes out."
        actions={
          <Link href="/guided-demo" className="btn btn-secondary">
            Replay the guided demo
          </Link>
        }
      />

      <div className="mx-auto max-w-3xl space-y-8 px-4 py-6 sm:px-6 sm:py-10 lg:px-8">
        <section className="surface-card p-6">
          <h2 className="text-lg font-semibold text-slate-900">
            What a pilot looks like
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            We are lining up a small number of civil and AEC firms as design
            partners. The goal is to run the review-support workflow against your
            real pre-submittal QA process, learn where it helps, and improve it
            together. Civil Engineer AI organizes review-support evidence and
            flags potential issues; a qualified professional remains responsible
            for every item.
          </p>
          <ul className="mt-4 space-y-2 text-sm text-slate-700">
            <li>Tell us about your firm and your current review bottleneck.</li>
            <li>We follow up to scope a pilot before requesting any files.</li>
            <li>
              You stay in control of your data; we do not collect project files
              on this page.
            </li>
          </ul>
        </section>

        <PilotRequestForm />

        <SafetyBoundaryBanner variant="compact" />
      </div>
    </div>
  );
}
