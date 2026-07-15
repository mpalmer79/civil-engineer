import Image from "next/image";
import Link from "next/link";

import { brooksideProjectImage, productPathways } from "@/components/home/content";

// Professional evaluation pathways: the guided product tour, the technical
// validation, the architecture documentation, and the pilot request. External
// pathways (repository documentation) render as anchors; internal pathways
// use client-side navigation.
export default function ProductPathways() {
  return (
    <section
      aria-labelledby="review-paths-heading"
      className="border-b border-slate-100 bg-slate-50"
    >
      <div className="mx-auto max-w-6xl px-4 pb-5 pt-12 sm:px-6 sm:pb-6 lg:px-8">
        <h2
          id="review-paths-heading"
          className="text-xl font-semibold text-slate-950"
        >
          Ways to evaluate the platform
        </h2>

        <p className="mt-1 max-w-3xl text-sm text-slate-600">
          Choose the pathway that fits your evaluation: a guided product tour,
          the reproducible technical validation, the architecture
          documentation, or a pilot request.
        </p>

        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {productPathways.map((pathway) => (
            <div
              key={pathway.title}
              className="flex flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-card"
            >
              <h3 className="text-sm font-semibold text-slate-900">
                {pathway.title}
              </h3>

              <p className="mt-2 flex-1 text-xs leading-relaxed text-slate-600">
                {pathway.detail}
              </p>

              {pathway.external ? (
                <a
                  href={pathway.href}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-flex text-xs font-semibold text-water-700 hover:underline"
                >
                  {pathway.linkLabel}
                </a>
              ) : (
                <Link
                  href={pathway.href}
                  className="mt-3 inline-flex text-xs font-semibold text-water-700 hover:underline"
                >
                  {pathway.linkLabel}
                </Link>
              )}
            </div>
          ))}
        </div>

        <figure className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card-lg">
          <div className="relative aspect-[16/9] w-full">
            <Image
              src={brooksideProjectImage.src}
              alt={brooksideProjectImage.alt}
              fill
              sizes="(max-width: 640px) calc(100vw - 32px), (max-width: 1024px) calc(100vw - 48px), 1152px"
              className="object-cover object-center"
            />
          </div>
        </figure>
      </div>
    </section>
  );
}
