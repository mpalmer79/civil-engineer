// Shared marketing media manifest.
//
// Stable, string-based public paths for the homepage and demo entry pages. The
// referenced image files may not be committed yet, so consumers must treat
// these as placeholder paths and provide a graceful fallback when an image is
// missing. Nothing here imports an image file directly, so a missing asset
// never breaks the build. Alt text is review-support only and carries no
// final-decision or approval language.
export const marketingMedia = {
  hero: {
    src: "/images/civil-engineer/site-plan-review-hero.webp",
    alt: "Illustrated stormwater review workspace showing a residential site plan, detention basin, evidence cards, and reviewer markers.",
  },
  workflow: {
    src: "/images/civil-engineer/review-workflow-visual.webp",
    alt: "Illustrated reviewer workflow from document intake through evidence review, response package, and dashboard.",
  },
  technicalFoundation: {
    src: "/images/civil-engineer/technical-foundation-visual.webp",
    alt: "Illustrated technical foundation showing frontend, backend, document storage, evidence retrieval, access control, and diagnostics.",
  },
  humanReviewBoundary: {
    src: "/images/civil-engineer/human-review-boundary.webp",
    alt: "Illustration of a human reviewer inspecting stormwater plan evidence with review-support indicators.",
  },
  guidedDemoJourney: {
    src: "/images/civil-engineer/guided-demo-journey.webp",
    alt: "Illustrated guided demo path through the Brookside Meadows reviewer journey.",
  },
} as const;

export type MarketingMediaKey = keyof typeof marketingMedia;
