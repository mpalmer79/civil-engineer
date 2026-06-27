"use client";

import { useState } from "react";

import SitePlanIllustration from "@/components/illustrations/SitePlanIllustration";

// Reusable marketing media slot.
//
// Renders an image from a string public path. The referenced files may not be
// committed yet, so when the image fails to load the broken image is hidden and
// a polished fallback panel is shown instead. The fallback reuses the existing
// visual system (surface styling, a subtle blueprint gradient, and the
// decorative site-plan line work) so the homepage looks intentional even before
// the real assets land. This is presentation only and carries no review-support
// state or final-decision language.

type MarketingMediaVariant = "hero" | "wide" | "panel";

// Aspect ratios per variant. Hero is a touch taller for the landing panel,
// wide is a standard 16:9 section image, panel is 4:3 for the boundary slot.
const variantAspect: Record<MarketingMediaVariant, string> = {
  hero: "aspect-[16/10]",
  wide: "aspect-[16/9]",
  panel: "aspect-[4/3]",
};

export default function MarketingMedia({
  src,
  alt,
  className = "",
  priority = false,
  variant = "wide",
  label = "Media placeholder",
}: {
  src: string;
  alt: string;
  className?: string;
  priority?: boolean;
  variant?: MarketingMediaVariant;
  label?: string;
}) {
  const [failed, setFailed] = useState(false);

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card ${variantAspect[variant]} ${className}`}
    >
      {failed ? (
        <MarketingMediaFallback alt={alt} label={label} />
      ) : (
        // A plain img with a string public path keeps the build resilient when
        // the asset is missing: there is no static import to resolve at build
        // time, and onError swaps in the fallback instead of a broken icon.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt={alt}
          loading={priority ? "eager" : "lazy"}
          decoding="async"
          onError={() => setFailed(true)}
          className="h-full w-full object-cover"
          data-testid="marketing-media-image"
        />
      )}
    </div>
  );
}

// Polished placeholder shown when the real asset is missing. It keeps the alt
// text accessible through role and aria-label so screen readers still get the
// description, and it never renders a broken image icon.
function MarketingMediaFallback({
  alt,
  label,
}: {
  alt: string;
  label: string;
}) {
  return (
    <div
      role="img"
      aria-label={alt}
      data-testid="marketing-media-fallback"
      className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-water-50 via-white to-slate-100"
    >
      <SitePlanIllustration className="pointer-events-none absolute inset-0 h-full w-full text-slate-500 opacity-[0.12]" />
      <div className="relative flex flex-col items-center gap-2 px-6 text-center">
        <span className="chip chip-brand">{label}</span>
        <p className="max-w-xs text-xs leading-relaxed text-slate-500">
          Optimized artwork will render here once added to the public media
          folder.
        </p>
      </div>
    </div>
  );
}
