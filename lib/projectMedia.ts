import { brooksideMedia } from "@/lib/brooksideMedia";

export const projectMedia = {
  hero: {
    src: "/images/civil-engineer/projects-hero-aerial.webp",
    alt: "Aerial view of a residential stormwater review project with roads, homes, and a central pond.",
  },
  // The Brookside aerial is owned by lib/brooksideMedia.ts; this entry only
  // re-exposes it so older imports keep working without a second registry.
  brooksideThumbnail: {
    src: brooksideMedia.image.src,
    alt: brooksideMedia.image.alt,
  },
  documentsPreview: {
    src: "/images/civil-engineer/project-documents-preview.webp",
    alt: "Preview of stormwater plan sheets and project documents prepared for review.",
  },
  reviewSnapshot: {
    src: "/images/civil-engineer/project-review-snapshot.webp",
    alt: "Review snapshot visual with findings, status indicators, and recent project activity.",
  },
  emptyProjects: {
    src: "/images/civil-engineer/empty-projects-illustration.webp",
    alt: "Illustration for an empty projects workspace with civil plans, a folder, and site review equipment.",
  },
} as const;
