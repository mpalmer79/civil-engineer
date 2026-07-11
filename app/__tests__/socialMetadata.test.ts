import { existsSync } from "node:fs";
import { join } from "node:path";

import type { Metadata } from "next";
import { afterEach, describe, expect, it, vi } from "vitest";

import { metadata as layoutMetadata } from "@/app/layout";
import { metadata as homeMetadata } from "@/app/page";
import { metadata as pocMetadata } from "@/app/proof-of-concept/page";
import { brooksideMedia } from "@/lib/brooksideMedia";
import { absoluteUrl, siteUrl } from "@/lib/siteUrl";

// Social metadata contract: absolute production URLs, the Brookside social
// preview as the link-preview image with declared 1200x630 dimensions, a
// summary_large_image Twitter card, and one canonical URL per public page.
// /proof-of-concept stays the canonical proof URL; /poc and /proofofconcept
// are redirects only and never appear as canonicals.

function ogImages(metadata: Metadata) {
  const images = metadata.openGraph?.images;
  return Array.isArray(images) ? images : [images];
}

describe("site URL helper", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("falls back to the deployed production origin", () => {
    expect(siteUrl()).toBe("https://civil-engineer.up.railway.app");
  });

  it("honors NEXT_PUBLIC_SITE_URL and strips trailing slashes", () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "https://example.org/");
    expect(siteUrl()).toBe("https://example.org");
    expect(absoluteUrl("/start-here")).toBe("https://example.org/start-here");
  });
});

describe("layout metadata", () => {
  it("sets an absolute HTTPS metadataBase", () => {
    const base = layoutMetadata.metadataBase as URL;
    expect(base).toBeInstanceOf(URL);
    expect(base.protocol).toBe("https:");
  });

  it("uses the Brookside social preview with 1200x630 dimensions and alt text", () => {
    const [image] = ogImages(layoutMetadata) as Array<{
      url: string;
      width: number;
      height: number;
      alt: string;
    }>;
    expect(image.url).toBe(brooksideMedia.socialPreview.src);
    expect(image.width).toBe(1200);
    expect(image.height).toBe(630);
    expect(image.alt).toBe(brooksideMedia.socialPreview.alt);
  });

  it("declares the Open Graph site name and a summary_large_image card", () => {
    expect(layoutMetadata.openGraph?.siteName).toBe("Civil Engineer AI");
    expect(
      (layoutMetadata.twitter as { card?: string } | undefined)?.card,
    ).toBe("summary_large_image");
    expect(layoutMetadata.twitter?.images).toEqual([
      brooksideMedia.socialPreview.src,
    ]);
  });
});

describe("page canonicals", () => {
  const cases: Array<{ name: string; metadata: Metadata; canonical: string }> =
    [
      { name: "homepage", metadata: homeMetadata, canonical: "/" },
      {
        name: "proof of concept",
        metadata: pocMetadata,
        canonical: "/proof-of-concept",
      },
    ];

  it("sets the expected canonical per statically importable page", () => {
    for (const testCase of cases) {
      expect(testCase.metadata.alternates?.canonical).toBe(testCase.canonical);
      expect(testCase.metadata.openGraph?.url).toBe(testCase.canonical);
    }
  });

  it("sets canonicals on the dynamic demo pages", async () => {
    const [startHere, guidedDemo, projects] = await Promise.all([
      import("@/app/start-here/page"),
      import("@/app/guided-demo/page"),
      import("@/app/projects/page"),
    ]);
    expect(startHere.metadata.alternates?.canonical).toBe("/start-here");
    expect(guidedDemo.metadata.alternates?.canonical).toBe("/guided-demo");
    expect(projects.metadata.alternates?.canonical).toBe("/projects");
  });

  it("resolves canonicals to absolute production URLs", () => {
    const base = layoutMetadata.metadataBase as URL;
    const resolved = new URL("/proof-of-concept", base).href;
    expect(resolved).toMatch(/^https:\/\//);
    expect(resolved.endsWith("/proof-of-concept")).toBe(true);
  });

  it("keeps every page pointing at the shared social preview", async () => {
    const modules = await Promise.all([
      import("@/app/start-here/page"),
      import("@/app/guided-demo/page"),
      import("@/app/projects/page"),
    ]);
    for (const mod of [
      { metadata: homeMetadata },
      { metadata: pocMetadata },
      ...modules,
    ]) {
      const [image] = ogImages(mod.metadata as Metadata) as Array<{
        url: string;
      }>;
      expect(image.url).toBe(brooksideMedia.socialPreview.src);
    }
  });
});

describe("brookside media files", () => {
  it("commits both the original and the social preview", () => {
    expect(
      existsSync(join(process.cwd(), "public", brooksideMedia.image.src)),
    ).toBe(true);
    expect(
      existsSync(
        join(process.cwd(), "public", brooksideMedia.socialPreview.src),
      ),
    ).toBe(true);
  });
});
