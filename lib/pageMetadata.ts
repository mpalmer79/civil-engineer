import type { Metadata } from "next";

import { brooksideMedia } from "@/lib/brooksideMedia";

// Shared metadata builder. Next.js replaces (not deep-merges) the openGraph
// and twitter objects when a page redefines them, so every page-level
// metadata export goes through this helper to keep the social preview image,
// site name, and card type consistent with app/layout.tsx.

export const SITE_NAME = "Civil Engineer AI";
export const DEFAULT_TITLE = "Civil Engineer AI: Stormwater Review Assistant";
export const DEFAULT_DESCRIPTION =
  "Document-first, evidence-first, reviewer-controlled stormwater review-support platform for municipal and civil engineering plan review. Real project records, document storage, PDF page indexing, evidence citations and retrieval, checklist review, applicant response matrix, resubmittal rounds, and reviewer response packages. Brookside Meadows is the public guided demo fixture.";

export function pageMetadata({
  title,
  description,
  path,
}: {
  title: string;
  description: string;
  // Route path starting with "/". Resolved against metadataBase, so the
  // rendered canonical and og:url are absolute production URLs.
  path: string;
}): Metadata {
  return {
    title,
    description,
    alternates: {
      canonical: path,
    },
    openGraph: {
      type: "website",
      siteName: SITE_NAME,
      title,
      description,
      url: path,
      images: [
        {
          url: brooksideMedia.socialPreview.src,
          width: brooksideMedia.socialPreview.width,
          height: brooksideMedia.socialPreview.height,
          alt: brooksideMedia.socialPreview.alt,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [brooksideMedia.socialPreview.src],
    },
  };
}
