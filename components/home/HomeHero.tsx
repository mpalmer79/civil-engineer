import Image from "next/image";
import Link from "next/link";

import DemoDataBadge from "@/components/DemoDataBadge";
import { heroImage } from "@/components/home/content";

// Homepage hero: the product positioning headline, the primary and secondary
// calls to action, and the labeled synthetic reference-project hero image.
export default function HomeHero() {
  return (
    <section
      aria-labelledby="home-hero-heading"
      className="border-b border-slate-100 bg-gradient-to-b from-slate-50 to-white"
    >
      <div className="mx-auto max-w-6xl px-4 pb-12 pt-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-semibold uppercase tracking-wider text-water-700">
            Stormwater review support
          </p>

          <h1
            id="home-hero-heading"
            className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl"
          >
            Review stormwater submissions with evidence, context, and human
            control.
          </h1>

          <p className="mt-4 text-base leading-relaxed text-slate-600">
            Civil Engineer AI organizes project documents, plan references,
            review findings, applicant responses, and revision history for
            municipal stormwater reviewers. It supports the review; a licensed
            engineer makes every decision.
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/guided-demo"
              className="rounded-lg bg-water-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-water-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-water-600"
            >
              Start the Brookside Meadows Guided Demo
            </Link>

            <Link
              href="/start-here"
              className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-water-600"
            >
              Review the Technical Overview
            </Link>
          </div>
        </div>

        <figure className="mx-auto mt-10 max-w-4xl">
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card-lg">
            <div className="relative aspect-[16/9] w-full">
              <Image
                src={heroImage.src}
                alt={heroImage.alt}
                fill
                priority
                sizes="(max-width: 768px) 100vw, 896px"
                className="object-cover object-center"
              />
            </div>
          </div>

          <figcaption className="mt-3 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500">
            <DemoDataBadge label="Synthetic reference project" />

            <span>
              Brookside Meadows is a fictional 47-lot subdivision in the
              fictional Town of Hartwell. It is not a real project or a real
              approval.
            </span>
          </figcaption>
        </figure>
      </div>
    </section>
  );
}
