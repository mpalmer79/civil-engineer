# Brookside Visual System

The Brookside Meadows conceptual aerial is the single case-study visual for
the public demo surfaces. Brookside Meadows is a synthetic public demo
fixture; the visual is a conceptual rendering and never represents a real
development, survey, approved design, or constructed development.

## Source image

- Path: `public/images/civil-engineer/brookside-project-thumbnail.webp`
- Verified dimensions: 1672 x 941
- Format: WebP (lossy VP8)
- File size: 709,952 bytes
- The source file is never modified. Derivatives are generated from it by
  script.

## Social derivative

- Path: `public/images/civil-engineer/brookside-social-preview.webp`
- Dimensions: exactly 1200 x 630 (LinkedIn and Open Graph large-card size)
- Format: WebP (lossy VP8)
- File size: 248,560 bytes (documented ceiling: 350 KB)
- No text overlay is added.

### Crop decision

The source is 16:9 and the target is 40:21, so the derivative loses vertical
content. The generator extracts the largest integer-edged 40:21 window
(1640 x 861), centered horizontally and anchored to the bottom edge
(left 16, top 80). This preserves the stormwater pond, the surrounding
subdivision, and the lower-left Brookside title block, trimming only sky and
treeline from the top.

### Generation command

```
npm run media:generate   # scripts/generate-brookside-social-preview.mjs
npm run media:verify     # scripts/verify-brookside-media.mjs
```

`media:generate` is deterministic: the same source, options, and sharp
version produce byte-identical output. `media:verify` checks that both files
exist, parse as valid WebP, match the declared dimensions (1672 x 941 and
1200 x 630), stay within the documented size limit, and that every path
referenced by `lib/brooksideMedia.ts` exists in `public/`.

## Source of truth

`lib/brooksideMedia.ts` owns the image paths, verified dimensions, alt text,
disclosure copy, and the proof-of-concept caption. `lib/projectMedia.ts`
re-exposes the thumbnail entry from it for older imports; no second registry
exists. All rendering goes through `components/BrooksideProjectVisual.tsx`.

## Page placements

| Page | Variant | Notes |
| --- | --- | --- |
| `/start-here` | `feature` | Two-column layout in the "What is Brookside Meadows?" section; image stacks above the text on mobile. Keeps the Start Guided Demo and Open Brookside Meadows actions. |
| `/proof-of-concept` | `proof` | Inside the "What was tested" section with the DXF-distinction caption. |
| `/guided-demo` | `demo-cover` | Restrained cover section with the "Brookside Meadows Guided Review" heading; the first demo action stays reachable. Marked `priority` as the likely LCP image. |
| `/projects` | `card` | Demo fixture card only. Real project records render as rows with no Brookside imagery. |
| `/` (homepage) | none | The homepage hero keeps the product illustration; the Brookside aerial explains the case study, not the product. |

## Alt text

> Conceptual aerial visualization of the synthetic Brookside Meadows
> residential subdivision surrounding a stormwater pond.

## Disclosure

Visible figcaption on the framed variants (Start Here and the Guided Demo
cover):

> Synthetic case-study visualization. Not a real project, survey, approved
> design, or constructed development.

The projects card carries a screen-reader-only variant of the same
disclosure. The projects workspace bans final-decision vocabulary outright,
including inside negative statements, so the card wording omits that
vocabulary while keeping the meaning:

> Synthetic Brookside Meadows case-study visualization. Not a real project,
> survey, or constructed development.

Proof-of-concept caption (keeps the visual distinct from the DXF):

> This visualization communicates the fictional Brookside Meadows project
> context. The downloadable DXF is a separately generated test drawing used
> to exercise the real upload and parsing pipeline.

## Metadata configuration

`app/layout.tsx` sets `metadataBase` from `lib/siteUrl.ts`:
`NEXT_PUBLIC_SITE_URL` (origin only, no trailing path) when set, otherwise
the deployed frontend origin `https://civil-engineer.up.railway.app`. The
`pageMetadata` helper in `lib/pageMetadata.ts` gives every public page an
Open Graph block (site name, title, description, canonical URL, and the
1200 x 630 social preview with alt text) plus a `summary_large_image`
Twitter card. Canonical URLs: `/`, `/start-here`, `/guided-demo`,
`/proof-of-concept`, `/projects`. `/proof-of-concept` is the canonical proof
URL; `/poc` and `/proofofconcept` permanently redirect to it.

## Performance

The image is never preloaded globally. Only the guided-demo cover uses
`priority` (above the fold, likely LCP). Framed variants render with
intrinsic dimensions so the layout never shifts, one image element serves
all breakpoints through responsive `sizes`, and captions render below the
image, never over it.

## Live verification command

```
npm run verify:live -- --frontend https://civil-engineer.up.railway.app
```

The script checks the public routes, the `/poc` and `/proofofconcept`
redirects, both Brookside images (200 and `image/webp`), the homepage
og:image (absolute HTTPS, 1200 x 630, alt text), the Twitter card, canonical
URLs, and the presence of the visual and its required wording on Start Here,
Proof of Concept, and the Guided Demo.
