import Image from "next/image";

import { brooksideMedia } from "@/lib/brooksideMedia";

// The one component that renders the Brookside Meadows conceptual aerial.
// Path, dimensions, alt text, and captions come from lib/brooksideMedia.ts so
// no placement can drift. Variants cover the current placements only:
//
//   feature     Start Here "What is Brookside Meadows?" two-column section
//   proof       Proof of Concept, with the DXF-distinction caption
//   demo-cover  Guided Demo cover section
//   card        Projects workspace demo project card (fill layout)
//
// Every variant is a semantic figure with a figcaption. The framed variants
// use the intrinsic image dimensions so the browser reserves the box and the
// page never shifts when the image decodes. Captions render below the image,
// never over it.

export type BrooksideVisualVariant = "feature" | "proof" | "demo-cover" | "card";

const framedSizes: Record<Exclude<BrooksideVisualVariant, "card">, string> = {
  feature: "(min-width: 1024px) 45vw, (min-width: 640px) 90vw, 100vw",
  proof: "(min-width: 1024px) 768px, (min-width: 640px) 90vw, 100vw",
  "demo-cover": "(min-width: 1024px) 40vw, (min-width: 640px) 90vw, 100vw",
};

export default function BrooksideProjectVisual({
  variant,
  className = "",
  priority = false,
}: {
  variant: BrooksideVisualVariant;
  className?: string;
  // Set only when the placement is above the fold and the likely LCP image.
  priority?: boolean;
}) {
  if (variant === "card") {
    // Fill layout for the projects demo card: the parent link controls the
    // box, and the disclosure stays available to assistive technology.
    return (
      <figure
        data-testid="brookside-project-visual"
        data-variant={variant}
        className={`relative m-0 h-40 w-full sm:h-52 ${className}`}
      >
        <Image
          src={brooksideMedia.image.src}
          alt={brooksideMedia.image.alt}
          fill
          sizes="(min-width: 1024px) 33vw, 100vw"
          className="object-cover"
        />
        <figcaption className="sr-only">
          {brooksideMedia.cardDisclosure}
        </figcaption>
      </figure>
    );
  }

  const caption =
    variant === "proof" ? brooksideMedia.proofCaption : brooksideMedia.disclosure;

  return (
    <figure
      data-testid="brookside-project-visual"
      data-variant={variant}
      className={`m-0 ${className}`}
    >
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-card">
        <Image
          src={brooksideMedia.image.src}
          alt={brooksideMedia.image.alt}
          width={brooksideMedia.image.width}
          height={brooksideMedia.image.height}
          sizes={framedSizes[variant]}
          priority={priority}
          className="h-auto w-full"
        />
      </div>
      <figcaption className="mt-2 text-xs leading-5 text-slate-500">
        {caption}
      </figcaption>
    </figure>
  );
}
