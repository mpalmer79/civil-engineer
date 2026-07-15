import Image from "next/image";
import Link from "next/link";

import DemoDataBadge from "@/components/DemoDataBadge";
import { workspaceImage } from "@/components/home/content";

// The DXF-to-review workflow showcase: how drawing data becomes
// reviewer-ready evidence, with a link to the reproducible technical
// validation.
export default function DxfShowcase() {
  return (
    <section
      aria-labelledby="dxf-workspace-heading"
      className="border-b border-slate-100 bg-white"
    >
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        <div className="grid items-center gap-8 lg:grid-cols-12 lg:gap-12">
          <div className="lg:order-2 lg:col-span-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-water-700">
              DXF-to-review workflow
            </p>

            <h2
              id="dxf-workspace-heading"
              className="mt-3 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl"
            >
              Turn drawing data into reviewer-ready evidence.
            </h2>

            <p className="mt-4 text-sm leading-relaxed text-slate-600">
              The reproducible technical validation processes a synthetic
              subdivision DXF through the real upload and parsing services,
              checks extraction results against versioned ground truth, and
              publishes traceable review-support artifacts.
            </p>

            <p className="mt-4 text-sm leading-relaxed text-slate-600">
              Civil Engineer AI keeps drawing metadata, classified layers,
              extracted site information, findings, and supporting evidence
              connected to the project record. Engineering judgment, compliance
              decisions, and approval remain with the reviewer.
            </p>

            <div className="mt-6">
              <Link
                href="/proof-of-concept"
                className="inline-flex items-center rounded-lg bg-water-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-water-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-water-600"
              >
                Review the DXF Technical Validation
              </Link>
            </div>
          </div>

          <figure className="lg:order-1 lg:col-span-7">
            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 shadow-card-lg">
              <div className="relative aspect-[4/3] w-full">
                <Image
                  src={workspaceImage.src}
                  alt={workspaceImage.alt}
                  fill
                  sizes="(max-width: 1024px) 100vw, 672px"
                  className="object-cover object-center"
                />
              </div>
            </div>

            <figcaption className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <DemoDataBadge label="Synthetic reference project" />

              <span>
                Illustrative workspace using synthetic Brookside Meadows review
                materials.
              </span>
            </figcaption>
          </figure>
        </div>
      </div>
    </section>
  );
}
