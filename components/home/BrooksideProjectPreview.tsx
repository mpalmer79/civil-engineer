import Image from "next/image";

import { brooksideProjectImage } from "@/components/home/content";

// Standalone visual preview of the synthetic Brookside Meadows reference
// project. The image object (path and alt text) is shared from
// components/home/content.ts so it is never duplicated across sections.
export default function BrooksideProjectPreview() {
  return (
    <section
      aria-labelledby="brookside-preview-heading"
      className="border-b border-slate-100 bg-white"
    >
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <h2 id="brookside-preview-heading" className="sr-only">
          Brookside Meadows reference project preview
        </h2>
        <figure className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card-lg">
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
